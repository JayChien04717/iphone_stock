import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

import data_fetcher
import valuation


class ForecastEpsTest(unittest.TestCase):
    @patch('data_fetcher.yf.Ticker')
    def test_forecast_eps_uses_history_and_growth(self, mock_ticker):
        dummy = MagicMock()
        dummy.info = {
            'forwardEps': 5.5,
            'earningsGrowth': 0.1,
            'sharesOutstanding': 100
        }
        dummy.earnings = pd.DataFrame({'Earnings': [400, 500]}, index=[2022, 2023])
        mock_ticker.return_value = dummy

        result = data_fetcher.forecast_eps.__wrapped__('TEST', years=3)

        self.assertAlmostEqual(result['base_eps'], 5.0)
        self.assertEqual(len(result['forecast']), 3)
        self.assertAlmostEqual(result['forecast'][0]['eps'], 5.5, places=2)
        self.assertAlmostEqual(result['forecast'][-1]['eps'], 5.5 * (1.1 ** 2), places=2)


class ValuationMathTest(unittest.TestCase):
    def test_dcf_converts_eps_to_fcf(self):
        eps_forecast = [5.0, 5.25, 5.5125, 5.788125, 6.07753125]
        fair_value = valuation.calculate_dcf(
            None,
            shares_outstanding=100,
            discount_rate=0.1,
            growth_rate=0.05,
            terminal_growth_rate=0.02,
            eps_forecast=eps_forecast,
            eps_to_fcf_ratio=0.8
        )
        self.assertIsNotNone(fair_value)
        self.assertGreater(fair_value, 0)

    def test_peg_ratio_and_value(self):
        peg_ratio = valuation.calculate_peg_ratio(20, 0.1)
        peg_value = valuation.calculate_peg_value(5, 0.1)
        self.assertAlmostEqual(peg_ratio, 2.0)
        self.assertAlmostEqual(peg_value, 50.0)


if __name__ == '__main__':
    unittest.main()
