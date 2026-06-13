from rest_framework import serializers
from .models import Election, Candidate, Voter, Vote, AuditLog
from django.utils import timezone


class CandidateSerializer(serializers.ModelSerializer):
    vote_count = serializers.ReadOnlyField()
    vote_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Candidate
        fields = ['id', 'name', 'description', 'image_url', 'position', 'vote_count', 'vote_percentage', 'created_at']
        read_only_fields = ['id', 'created_at']


class CandidateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['name', 'description', 'image_url', 'position']


class ElectionListSerializer(serializers.ModelSerializer):
    total_votes = serializers.ReadOnlyField()
    candidate_count = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Election
        fields = ['id', 'title', 'description', 'start_date', 'end_date',
                  'status', 'is_active', 'total_votes', 'candidate_count',
                  'allow_multiple_votes', 'is_public_result', 'created_at']

    def get_candidate_count(self, obj):
        return obj.candidates.count()


class ElectionDetailSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)
    total_votes = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Election
        fields = ['id', 'title', 'description', 'start_date', 'end_date',
                  'status', 'is_active', 'candidates', 'total_votes',
                  'allow_multiple_votes', 'is_public_result', 'created_by',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ElectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ['title', 'description', 'start_date', 'end_date',
                  'allow_multiple_votes', 'is_public_result', 'created_by']

    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("end_date must be after start_date.")
        return data


class VoterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voter
        fields = ['id', 'voter_id', 'name', 'email', 'is_eligible', 'registered_at']
        read_only_fields = ['id', 'registered_at']


class VoterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voter
        fields = ['voter_id', 'name', 'email']

    def validate_voter_id(self, value):
        if Voter.objects.filter(voter_id=value).exists():
            raise serializers.ValidationError("Voter ID already registered.")
        return value

    def validate_email(self, value):
        if Voter.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value


class VoteSerializer(serializers.ModelSerializer):
    voter_name = serializers.CharField(source='voter.name', read_only=True)
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    election_title = serializers.CharField(source='candidate.election.title', read_only=True)

    class Meta:
        model = Vote
        fields = ['id', 'voter_name', 'candidate_name', 'election_title', 'voted_at']


class CastVoteSerializer(serializers.Serializer):
    voter_id = serializers.CharField()
    candidate_id = serializers.UUIDField()

    def validate(self, data):
        try:
            voter = Voter.objects.get(voter_id=data['voter_id'])
        except Voter.DoesNotExist:
            raise serializers.ValidationError({"voter_id": "Voter not found."})

        if not voter.is_eligible:
            raise serializers.ValidationError({"voter_id": "Voter is not eligible to vote."})

        try:
            candidate = Candidate.objects.select_related('election').get(id=data['candidate_id'])
        except Candidate.DoesNotExist:
            raise serializers.ValidationError({"candidate_id": "Candidate not found."})

        election = candidate.election
        election.auto_update_status()

        if not election.is_active:
            raise serializers.ValidationError({"election": "This election is not currently active."})

        if not election.allow_multiple_votes and voter.has_voted(election):
            raise serializers.ValidationError({"voter_id": "Voter has already cast a vote in this election."})

        data['voter'] = voter
        data['candidate'] = candidate
        data['election'] = election
        return data


class ElectionResultSerializer(serializers.ModelSerializer):
    candidates = serializers.SerializerMethodField()
    total_votes = serializers.ReadOnlyField()
    winner = serializers.SerializerMethodField()

    class Meta:
        model = Election
        fields = ['id', 'title', 'status', 'total_votes', 'winner', 'candidates']

    def get_candidates(self, obj):
        candidates = obj.candidates.all()
        return sorted([
            {
                'id': str(c.id),
                'name': c.name,
                'vote_count': c.vote_count,
                'vote_percentage': c.vote_percentage,
            }
            for c in candidates
        ], key=lambda x: x['vote_count'], reverse=True)

    def get_winner(self, obj):
        if obj.status != 'closed':
            return None
        candidates = list(obj.candidates.all())
        if not candidates:
            return None
        winner = max(candidates, key=lambda c: c.vote_count)
        if winner.vote_count == 0:
            return None
        return {'id': str(winner.id), 'name': winner.name, 'vote_count': winner.vote_count}


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'action', 'actor', 'details', 'timestamp', 'ip_address']
