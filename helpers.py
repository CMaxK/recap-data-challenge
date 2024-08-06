import requests
import json
import pandas as pd


BASE_URL = "https://nookdtmzylu7w75p7atatnzom40zmdpz.lambda-url.eu-central-1.on.aws/invoices"

def fetch_all_invoices():
    """
    Function to handle retrieval of invoices from aws endpoint.
    Returns data as JSON object
    """
    invoices = []
    page = 1
    total_pages = 1  # allows matching of current page with amx page

    while page <= total_pages:
        try:
            response = requests.get(f"{BASE_URL}?page={page}")
            # Raise an HTTPError for bad responses (4xx, 5xx, etc.)
            response.raise_for_status()

            response_data = response.json()
            if response_data.get("status_code") != 200:
                print(
                    f"Error: Status code {response_data.get('status_code')} on page {page}"
                )
                break

            data = response_data.get("body", {}).get("data", [])
            total_pages = response_data.get("body", {}).get("total_pages", 1)

            if not data and page > total_pages:
                break

            # for testing
            # print(f"Finished fetching page {page}")
            invoices.extend(data)
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    return invoices


def save_invoices_to_file(invoices, filename="data/invoices.json"):
    """
    Writes invoices to file called invoices.json
    """
    with open(filename, "w") as f:
        json.dump(invoices, f, indent=4)


def preprocess_invoices(invoices):
    """
    Handles grouping and aggregating of monthly revenus for each contract_id
    """
    df = pd.DataFrame(invoices)
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])

    # create a new 'month' column
    df["month"] = df["invoice_date"].dt.to_period("M")

    # group by contract_id and month, sum the original_billing_amount
    df = (
        df.groupby(["contract_id", "month"])
        .agg({"original_billing_amount": "sum"})
        .reset_index()
    )

    df.rename(columns={"original_billing_amount": "net_revenue"}, inplace=True)

    # not strictly necessary as previous grouping handles sorting already
    df = df.sort_values(by=["contract_id", "month"])

    return df


def compute_net_revenue_and_churn(df):
    """
    Creates churn value by obtaining difference between monthly net_revenue per
    contract.
    Outputs cleaned DF
    """
    df["previous_net_revenue"] = (
        df.groupby("contract_id")["net_revenue"].shift().fillna(0)
    )

    # Calculate churned amount
    df["churned_amount"] = df.apply(
        lambda row: (
            row["previous_net_revenue"] - row["net_revenue"]
            if row["previous_net_revenue"] > row["net_revenue"]
            else 0
        ),
        axis=1,
    )

    df = df.drop(columns=["previous_net_revenue"])
    df["net_revenue"] = df["net_revenue"].round(2)
    df["churned_amount"] = df["churned_amount"].round(2)

    # Final formatting
    df["month"] = df["month"].astype(str)

    return df


def save_net_revenue_churn_to_file(df, filename="data/net_revenue_churn.csv"):
    """
    Writes final DF to local file for possible further EDA
    """
    df.to_csv(filename, index=False)
