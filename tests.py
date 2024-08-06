import unittest
from unittest.mock import patch, MagicMock
from helpers import (
    fetch_all_invoices,
    preprocess_invoices,
    compute_net_revenue_and_churn,
)


class TestInvoiceProcessing(unittest.TestCase):

    @patch("helpers.requests.get")
    def test_fetch_all_invoices(self, mock_get):
        """
        Tests fetch_all_invoices function  by mocking return values in simple format
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status_code": 200,
            "body": {
                "data": [
                    {
                        "invoice_date": "2021-11-01",
                        "contract_id": "A",
                        "original_billing_amount": 200,
                    }
                ],
                "total_pages": 1,
                "page": 1,
            },
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        invoices = fetch_all_invoices()
        self.assertIsInstance(invoices, list)
        # ensures data was fetched
        self.assertGreater(len(invoices), 0)
        self.assertEqual(invoices[0]["contract_id"], "A")

    def test_preprocess_invoices(self):
        """
        Tests correct grouping and aggregating of monthly revenus for each unique contract_id
        """
        invoices = [
            {
                "invoice_date": "2021-11-01",
                "contract_id": "A",
                "original_billing_amount": 200,
            },
            {
                "invoice_date": "2021-11-15",
                "contract_id": "A",
                "original_billing_amount": 150,
            },
            {
                "invoice_date": "2021-12-01",
                "contract_id": "B",
                "original_billing_amount": 100,
            },
            {
                "invoice_date": "2021-12-20",
                "contract_id": "B",
                "original_billing_amount": 50,
            },
        ]
        df = preprocess_invoices(invoices)
        self.assertEqual(len(df), 2)
        self.assertEqual(df[df["contract_id"] == "A"]["net_revenue"].iloc[0], 350)
        self.assertEqual(df[df["contract_id"] == "B"]["net_revenue"].iloc[0], 150)

    def test_compute_net_revenue_and_churn(self):
        """
        Tests calculation of churn values
        """
        invoices = [
            {
                "invoice_date": "2021-11-01",
                "contract_id": "A",
                "original_billing_amount": 200,
            },
            {
                "invoice_date": "2021-12-01",
                "contract_id": "A",
                "original_billing_amount": 200,
            },
            {
                "invoice_date": "2022-01-01",
                "contract_id": "A",
                "original_billing_amount": 0,
            },
            {
                "invoice_date": "2022-02-01",
                "contract_id": "A",
                "original_billing_amount": 0,
            },
        ]
        df = preprocess_invoices(invoices)
        net_revenue = compute_net_revenue_and_churn(df)
        self.assertEqual(len(net_revenue), 4)
        self.assertEqual(net_revenue.iloc[2]["churned_amount"], 200)
        self.assertEqual(net_revenue.iloc[3]["churned_amount"], 0)
        self.assertNotIn("previous_net_revenue", net_revenue.columns)
        self.assertAlmostEqual(net_revenue["net_revenue"].iloc[0], 200.00)
        self.assertAlmostEqual(net_revenue["churned_amount"].iloc[2], 200.00)


if __name__ == "__main__":
    unittest.main()
