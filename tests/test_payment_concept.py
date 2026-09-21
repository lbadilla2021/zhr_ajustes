from datetime import date

from odoo.tests.common import TransactionCase


class TestPaymentConcept(TransactionCase):
    def test_payment_concept_stores_new_free_text_fields(self):
        concept = self.env['hr.payment.concept'].create({
            'name': 'Bono especial',
            'description': 'Descripcion del beneficio.',
            'target_group': 'Supervisores de planta',
            'value_text': '2,5 UF mensuales',
            'modification_date': date(2026, 9, 15),
        })

        self.assertEqual(concept.target_group, 'Supervisores de planta')
        self.assertEqual(concept.value_text, '2,5 UF mensuales')
        self.assertEqual(concept.modification_date, date(2026, 9, 15))

    def test_modification_date_is_configured_for_history(self):
        concept = self.env['hr.payment.concept'].create({
            'name': 'Bono con historial',
            'modification_date': date(2026, 1, 1),
        })

        concept.modification_date = date(2026, 6, 1)

        self.assertEqual(concept.modification_date, date(2026, 6, 1))
        self.assertIn('modification_date', concept._track_get_fields())
        self.assertTrue(concept._fields['modification_date'].tracking)

    def test_payment_concept_form_contains_change_history(self):
        arch = self.env['hr.payment.concept'].get_view(
            view_type='form'
        )['arch']

        self.assertIn('name="target_group"', arch)
        self.assertIn('name="value_text"', arch)
        self.assertIn('name="modification_date"', arch)
        self.assertIn('<chatter', arch)
