from django.core.management.base import BaseCommand
from django.utils import timezone
from elections.models import Election, Candidate, Voter, Vote
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')
        now = timezone.now()

        e1 = Election.objects.create(
            title='General Presidential Election 2024',
            description='National presidential election for the term 2024-2028.',
            start_date=now - timedelta(hours=2),
            end_date=now + timedelta(days=2),
            status='active',
            created_by='admin',
            is_public_result=True,
        )
        e2 = Election.objects.create(
            title='City Council Election',
            description='Local city council seat election.',
            start_date=now + timedelta(days=5),
            end_date=now + timedelta(days=10),
            status='draft',
            created_by='admin',
        )
        e3 = Election.objects.create(
            title='Student Union Election 2023',
            description='Annual student union representative election.',
            start_date=now - timedelta(days=10),
            end_date=now - timedelta(days=2),
            status='closed',
            created_by='admin',
            is_public_result=True,
        )

        c1 = Candidate.objects.create(election=e1, name='Alice Johnson', description='Progressive candidate focused on healthcare.', position=1)
        c2 = Candidate.objects.create(election=e1, name='Bob Martinez', description='Conservative candidate focused on economy.', position=2)
        c3 = Candidate.objects.create(election=e1, name='Carol Lee', description='Independent focused on environment.', position=3)
        Candidate.objects.create(election=e2, name='David Kim', description='Local business owner.', position=1)
        Candidate.objects.create(election=e2, name='Emma Wilson', description='School teacher and community activist.', position=2)
        c6 = Candidate.objects.create(election=e3, name='Frank Patel', description='Student tech enthusiast.', position=1)
        c7 = Candidate.objects.create(election=e3, name='Grace Chen', description='Arts and culture advocate.', position=2)

        voters = []
        for i in range(1, 16):
            v = Voter.objects.create(
                voter_id=f'VOT{i:04d}',
                name=f'Voter {i}',
                email=f'voter{i}@example.com',
                is_eligible=True,
            )
            voters.append(v)

        for i, voter in enumerate(voters[:10]):
            candidate = [c1, c2, c3][i % 3]
            Vote.objects.create(voter=voter, candidate=candidate, ip_address='127.0.0.1')

        for i, voter in enumerate(voters[5:]):
            candidate = [c6, c7][i % 2]
            Vote.objects.create(voter=voter, candidate=candidate, ip_address='127.0.0.1')

        self.stdout.write(self.style.SUCCESS('Sample data seeded!'))
