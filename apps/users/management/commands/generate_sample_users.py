from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate sample users for testing'

    def handle(self, *args, **options):
        # Sample users data
        users = [
            {
                'first_name': 'Juan',
                'last_name': 'Dela Cruz',
                'email': 'juan.delacruz@ispbilling.com',
                'username': 'juan.delacruz@ispbilling.com',
                'user_type': User.CASHIER,
                'is_active': True,
            },
            {
                'first_name': 'Ana',
                'last_name': 'Reyes',
                'email': 'ana.reyes@ispbilling.com',
                'username': 'ana.reyes@ispbilling.com',
                'user_type': User.CASHIER,
                'is_active': True,
            },
            {
                'first_name': 'Pedro',
                'last_name': 'Garcia',
                'email': 'pedro.garcia@ispbilling.com',
                'username': 'pedro.garcia@ispbilling.com',
                'user_type': User.TECHNICIAN,
                'is_active': True,
            },
            {
                'first_name': 'Carlos',
                'last_name': 'Martinez',
                'email': 'carlos.martinez@ispbilling.com',
                'username': 'carlos.martinez@ispbilling.com',
                'user_type': User.TECHNICIAN,
                'is_active': True,
            },
            {
                'first_name': 'Rosa',
                'last_name': 'Domingo',
                'email': 'rosa.domingo@ispbilling.com',
                'username': 'rosa.domingo@ispbilling.com',
                'user_type': User.TECHNICIAN,
                'is_active': True,
            },
            {
                'first_name': 'Jose',
                'last_name': 'Rizal',
                'email': 'jose.rizal@ispbilling.com',
                'username': 'jose.rizal@ispbilling.com',
                'user_type': User.CASHIER,
                'is_active': False,  # Inactive cashier
            },
        ]

        created_count = 0
        for user_data in users:
            email = user_data['email']
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=email,
                    password='testpass123',  # Default password for all test users
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    user_type=user_data['user_type'],
                    is_active=user_data['is_active'],
                )
                created_count += 1
                status = "Active" if user.is_active else "Inactive"
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {user.get_user_type_display()} user: {user.get_full_name()} ({status})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'User already exists: {email}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} users'
            )
        )
        
        if created_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    '\nNote: All test users have password "testpass123"'
                )
            )
