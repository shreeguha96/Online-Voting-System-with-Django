from django.db import models
from django.utils import timezone
import uuid


class Election(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, default='admin')
    allow_multiple_votes = models.BooleanField(default=False)
    is_public_result = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        now = timezone.now()
        return self.status == 'active' and self.start_date <= now <= self.end_date

    @property
    def total_votes(self):
        return Vote.objects.filter(candidate__election=self).count()

    def auto_update_status(self):
        now = timezone.now()
        if self.status == 'active' and now > self.end_date:
            self.status = 'closed'
            self.save()
        elif self.status == 'draft' and self.start_date <= now <= self.end_date:
            self.status = 'active'
            self.save()


class Candidate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position', 'name']
        unique_together = ['election', 'name']

    def __str__(self):
        return f"{self.name} ({self.election.title})"

    @property
    def vote_count(self):
        return self.votes.count()

    @property
    def vote_percentage(self):
        total = self.election.total_votes
        if total == 0:
            return 0.0
        return round((self.vote_count / total) * 100, 2)


class Voter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    voter_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    is_eligible = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.voter_id})"

    def has_voted(self, election):
        return Vote.objects.filter(voter=self, candidate__election=election).exists()


class Vote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    voted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-voted_at']
        unique_together = ['voter', 'candidate']

    def __str__(self):
        return f"{self.voter.name} → {self.candidate.name}"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('vote_cast', 'Vote Cast'),
        ('election_created', 'Election Created'),
        ('election_updated', 'Election Updated'),
        ('election_status_changed', 'Election Status Changed'),
        ('candidate_added', 'Candidate Added'),
        ('candidate_removed', 'Candidate Removed'),
        ('voter_registered', 'Voter Registered'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    actor = models.CharField(max_length=255)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} by {self.actor} at {self.timestamp}"
