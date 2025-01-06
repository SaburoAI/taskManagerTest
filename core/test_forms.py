from django.test import TestCase
from django.forms.models import model_to_dict
from .forms import CurriculumForm
from .models import TblCurriculum, TblSubject


class CurriculumFormTest(TestCase):

    def setUp(self):
        self.subject1 = TblSubject.objects.create(sub_name="Math")
        self.subject2 = TblSubject.objects.create(sub_name="Science")
        self.curriculum_data = {
            "curr_name": "Test Curriculum",
            "subjects": [self.subject1.id, self.subject2.id],
        }

    def test_valid_form(self):
        form = CurriculumForm(data=self.curriculum_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        invalid_data = self.curriculum_data.copy()
        invalid_data["curr_name"] = ""
        form = CurriculumForm(data=invalid_data)
        self.assertFalse(form.is_valid())

    def test_save_form(self):
        form = CurriculumForm(data=self.curriculum_data)
        self.assertTrue(form.is_valid())
        curriculum = form.save()
        self.assertEqual(curriculum.curr_name, "Test Curriculum")
        self.assertEqual(
            TblCurriculum.objects.count(), 3
        )  # 1 for '全体' and 2 for subjects
        self.assertEqual(TblCurriculum.objects.filter(sub_name="全体").count(), 1)
        self.assertEqual(TblCurriculum.objects.filter(sub_name="Math").count(), 1)
        self.assertEqual(TblCurriculum.objects.filter(sub_name="Science").count(), 1)
