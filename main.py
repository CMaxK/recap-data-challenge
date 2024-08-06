from helpers import fetch_all_invoices, save_invoices_to_file, preprocess_invoices, compute_net_revenue_and_churn, save_net_revenue_churn_to_file
def main():
    invoices = fetch_all_invoices()
    save_invoices_to_file(invoices)

    df = preprocess_invoices(invoices)
    net_revenue = compute_net_revenue_and_churn(df)
    save_net_revenue_churn_to_file(net_revenue)


if __name__ == "__main__":
    main()
