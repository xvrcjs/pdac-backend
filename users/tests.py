# tests.py

from django.conf import settings
from django.test import TestCase
from .models import User, Teacher, Account
from course.models import Course

class TeacherModelTestCase(TestCase):
    fixtures = ['db-initial.json']

    def setUp(self):
        # Crear un usuario
        self.user = User.objects.create_user(display_name='testuser', email='testuser@example.com', password='password')
        # Crear una cuenta
        self.account = Account.objects.create(user=self.user)
        # Crear cursos
        self.course1 = Course.objects.create(title='Course 1')

        self.course2 = Course.objects.create(title='Course 2')
        # Crear un maestro
        self.teacher = Teacher.objects.create(account=self.account)
        # Asignar cursos al maestro
        self.teacher.courses_assigned.add(self.course1, self.course2)

    def test_teacher_creation(self):
        """Prueba la creación del modelo Teacher"""
        self.assertEqual(str(self.teacher.account.user.email), self.user.email)

    def test_courses_assigned(self):
        """Prueba que los cursos se asignen correctamente al maestro"""
        self.assertEqual(self.teacher.courses_assigned.count(), 2)
        self.assertIn(self.course1, self.teacher.courses_assigned.all())
        self.assertIn(self.course2, self.teacher.courses_assigned.all())

    def test_teacher_account_relation(self):
        """Prueba la relación entre Teacher y Account"""
        self.assertEqual(self.teacher.account, self.account)
        self.assertEqual(self.teacher.account.user, self.user)