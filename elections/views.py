from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .models import Election, Candidate, Voter, Vote, AuditLog
from .serializers import (
    ElectionListSerializer, ElectionDetailSerializer, ElectionCreateSerializer,
    CandidateSerializer, CandidateCreateSerializer,
    VoterSerializer, VoterCreateSerializer,
    VoteSerializer, CastVoteSerializer,
    ElectionResultSerializer, AuditLogSerializer
)


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def log_action(action, actor, details, ip=None):
    AuditLog.objects.create(action=action, actor=actor, details=details, ip_address=ip)


class ElectionViewSet(viewsets.ModelViewSet):
    queryset = Election.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ElectionListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ElectionCreateSerializer
        return ElectionDetailSerializer

    def get_queryset(self):
        qs = Election.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        election = serializer.save()
        log_action('election_created', election.created_by,
                   {'election_id': str(election.id), 'title': election.title},
                   get_client_ip(self.request))

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        election = serializer.save()
        if old_status != election.status:
            log_action('election_status_changed', 'admin',
                       {'election_id': str(election.id), 'from': old_status, 'to': election.status},
                       get_client_ip(self.request))
        else:
            log_action('election_updated', 'admin',
                       {'election_id': str(election.id), 'title': election.title},
                       get_client_ip(self.request))

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        election = self.get_object()
        if election.status == 'active':
            return Response({'detail': 'Election is already active.'}, status=400)
        if election.status == 'closed':
            return Response({'detail': 'Cannot reactivate a closed election.'}, status=400)
        election.status = 'active'
        election.save()
        log_action('election_status_changed', 'admin',
                   {'election_id': str(election.id), 'from': 'draft', 'to': 'active'},
                   get_client_ip(request))
        return Response({'detail': 'Election activated successfully.'})

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request, pk=None):
        election = self.get_object()
        if election.status == 'closed':
            return Response({'detail': 'Election is already closed.'}, status=400)
        election.status = 'closed'
        election.save()
        log_action('election_status_changed', 'admin',
                   {'election_id': str(election.id), 'from': election.status, 'to': 'closed'},
                   get_client_ip(request))
        return Response({'detail': 'Election closed successfully.'})

    @action(detail=True, methods=['get'], url_path='results')
    def results(self, request, pk=None):
        election = self.get_object()
        election.auto_update_status()
        if not election.is_public_result and election.status != 'closed':
            return Response({'detail': 'Results are not public yet.'}, status=403)
        serializer = ElectionResultSerializer(election)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='voters')
    def voters(self, request, pk=None):
        election = self.get_object()
        voter_ids = Vote.objects.filter(
            candidate__election=election
        ).values_list('voter_id', flat=True).distinct()
        voters = Voter.objects.filter(id__in=voter_ids)
        serializer = VoterSerializer(voters, many=True)
        return Response({'count': voters.count(), 'voters': serializer.data})

    @action(detail=True, methods=['post'], url_path='candidates')
    def add_candidate(self, request, pk=None):
        election = self.get_object()
        if election.status == 'closed':
            return Response({'detail': 'Cannot add candidates to a closed election.'}, status=400)
        serializer = CandidateCreateSerializer(data=request.data)
        if serializer.is_valid():
            candidate = serializer.save(election=election)
            log_action('candidate_added', 'admin',
                       {'election_id': str(election.id), 'candidate': candidate.name},
                       get_client_ip(request))
            return Response(CandidateSerializer(candidate).data, status=201)
        return Response(serializer.errors, status=400)


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.select_related('election').all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CandidateCreateSerializer
        return CandidateSerializer

    def perform_create(self, serializer):
        candidate = serializer.save()
        log_action('candidate_added', 'admin',
                   {'candidate': candidate.name, 'election': candidate.election.title},
                   get_client_ip(self.request))

    def destroy(self, request, *args, **kwargs):
        candidate = self.get_object()
        election = candidate.election
        if election.status == 'active':
            return Response({'detail': 'Cannot remove candidate from an active election.'}, status=400)
        name = candidate.name
        candidate.delete()
        log_action('candidate_removed', 'admin',
                   {'candidate': name, 'election': election.title},
                   get_client_ip(request))
        return Response(status=204)


class VoterViewSet(viewsets.ModelViewSet):
    queryset = Voter.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return VoterCreateSerializer
        return VoterSerializer

    def perform_create(self, serializer):
        voter = serializer.save()
        log_action('voter_registered', 'system',
                   {'voter_id': voter.voter_id, 'name': voter.name},
                   get_client_ip(self.request))

    @action(detail=True, methods=['get'], url_path='vote-history')
    def vote_history(self, request, pk=None):
        voter = self.get_object()
        votes = voter.votes.select_related('candidate__election').all()
        serializer = VoteSerializer(votes, many=True)
        return Response({'voter': voter.name, 'votes': serializer.data})

    @action(detail=True, methods=['get'], url_path='check-eligibility/(?P<election_id>[^/.]+)')
    def check_eligibility(self, request, pk=None, election_id=None):
        voter = self.get_object()
        election = get_object_or_404(Election, id=election_id)
        election.auto_update_status()
        return Response({
            'voter': voter.name,
            'election': election.title,
            'is_eligible': voter.is_eligible,
            'has_voted': voter.has_voted(election),
            'can_vote': voter.is_eligible and not voter.has_voted(election) and election.is_active
        })


class VoteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vote.objects.select_related('voter', 'candidate__election').all()
    serializer_class = VoteSerializer

    @action(detail=False, methods=['post'], url_path='cast')
    def cast(self, request):
        serializer = CastVoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        voter = serializer.validated_data['voter']
        candidate = serializer.validated_data['candidate']
        election = serializer.validated_data['election']
        ip = get_client_ip(request)

        vote = Vote.objects.create(voter=voter, candidate=candidate, ip_address=ip)
        log_action('vote_cast', voter.voter_id,
                   {'election_id': str(election.id), 'candidate': candidate.name,
                    'election': election.title},
                   ip)

        return Response({
            'message': 'Vote cast successfully!',
            'vote_id': str(vote.id),
            'voter': voter.name,
            'candidate': candidate.name,
            'election': election.title,
            'voted_at': vote.voted_at,
        }, status=201)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.all()
        action_filter = self.request.query_params.get('action')
        if action_filter:
            qs = qs.filter(action=action_filter)
        actor = self.request.query_params.get('actor')
        if actor:
            qs = qs.filter(actor__icontains=actor)
        return qs


class DashboardView(viewsets.ViewSet):
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        from django.utils import timezone
        now = timezone.now()
        elections = Election.objects.all()
        for e in elections:
            e.auto_update_status()

        return Response({
            'total_elections': Election.objects.count(),
            'active_elections': Election.objects.filter(status='active').count(),
            'closed_elections': Election.objects.filter(status='closed').count(),
            'draft_elections': Election.objects.filter(status='draft').count(),
            'total_voters': Voter.objects.count(),
            'eligible_voters': Voter.objects.filter(is_eligible=True).count(),
            'total_votes_cast': Vote.objects.count(),
            'total_candidates': Candidate.objects.count(),
        })
