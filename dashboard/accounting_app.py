import streamlit as st
from datetime import date
from accounting.transaction import Transaction, TransactionType
from accounting.cash_flow import CashFlow, Visualizer, NoTransactionIDFound
import PIL
import io
import fitz
import base64
from typing import List


def base64_to_pil(image_b64):
    return PIL.Image.open(io.BytesIO(base64.b64decode(image_b64)))


def pil_to_base64(image) -> str:
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    img_b64 = base64.b64encode(stream.getvalue()).decode("utf-8")
    return img_b64


def get_file(file) -> List[str]:
    # To read file as bytes:
    bytes_data = file.getvalue()
    try:
        images = [PIL.Image.open(io.BytesIO(bytes_data))]
    except PIL.UnidentifiedImageError:
        pdf = fitz.open("pdf", bytes_data)
        zoom = 2
        mat = fitz.Matrix(zoom, zoom)
        images = []
        for i, pdf_page in enumerate(pdf):
            pix = pdf_page.get_pixmap(matrix=mat)
            images.append(PIL.Image.open(io.BytesIO(pix.tobytes())))
            
    images_b64 = []
    for image in images:
        images_b64.append(pil_to_base64(image))
        
    return images_b64


def app():
    
    cash_flow = CashFlow(
        past_transactions_path="accounting/past_transactions.json",
    )

    st.title("Accounting")

    st.sidebar.write("- Number of Transactions: ", len(cash_flow))
    df_payments = cash_flow.dataframe().query("Description == 'Amazon payment'")
    number_of_amazon_payments = len(df_payments)
    st.sidebar.write("- Number of Amazon Payments: ", number_of_amazon_payments)

    with st.sidebar:
        with st.form("insert-transaction"):
            st.header("**Insert Transaction**")
            transaction_type = st.selectbox(
                "Tipo", 
                options=[
                    x.name.capitalize() 
                    for x in TransactionType 
                    if x != TransactionType.PROFIT
                ],
            )
            transaction_date = st.date_input("Date", max_value=date.today())
            transaction_amount = st.number_input("Amount")
            transation_description = st.text_input("Description")
            transaction_file = st.file_uploader(
                "Upload Documents", 
                type=["PNG", "JPG", "PDF"], 
            )
            submit_transaction = st.form_submit_button("Submit")
        
        if submit_transaction:
            if transaction_file is not None:
                transaction_images_b64 = get_file(transaction_file)
            else:
                transaction_images_b64 = None

            transaction = Transaction(
                type=TransactionType[transaction_type.upper()],
                date=transaction_date,
                amount=transaction_amount,
                description= transation_description,
                file=transaction_images_b64,
            )
            cash_flow.add_transaction(transaction)
            cash_flow.dump(cash_flow.parsable_transactions())
            st.success("Transação added with success.")
            st.experimental_rerun()
        
        with st.form("remove-transaction"):
            st.header("**Remove Transaction**")
            transaction_id = st.number_input("Transaction ID", step=1)
            remove_transaction = st.form_submit_button("Submit")
        
        if remove_transaction:
            try:
                cash_flow.remove_transaction_by_id(transaction_id)
            except NoTransactionIDFound:
                st.error("Transaction ID not found.")
            else:
                cash_flow.dump(cash_flow.parsable_transactions())
                st.success("Transaction removed with success.")
                st.experimental_rerun()

        with st.form("insert-amazon-payment"):
            st.header("**Insert Amazon Payment**")
            payment_amount = st.number_input("Amount")
            payment_date = st.date_input("Date", max_value=date.today())
            payment_number_units = st.number_input(
                "Number Units Sold",
                min_value=0,
                step=1,
            )
            payment_cost_per_unit = st.number_input(
                "Cost per Unit Sold", 
                min_value=0.0,
            )
            payment_file = st.file_uploader(
                "Carregar Recibo", 
                type=["PNG", "JPG", "PDF"], 
            )
            submit_payment = st.form_submit_button("Submit")
            
        if submit_payment:
            if payment_file is not None:
                payment_images_b64 = get_file(payment_file)
            else:
                payment_images_b64 = None
            
            cash_flow.amazon_payment(
                amount=payment_amount,
                date=payment_date,
                number_units_sold=payment_number_units,
                cost_per_unit=payment_cost_per_unit,
                receipt=payment_images_b64, 
            )
            cash_flow.dump(cash_flow.parsable_transactions())
            st.success("Amazon Payment Added with Success.")
            st.experimental_rerun()


    viz = Visualizer(cash_flow)

    st.header("Operational Balance (Accrual Based)")
    fig_operations, _ = viz.display_per_transaction_type(TransactionType.OPERATIONS)
    st.plotly_chart(fig_operations)

    st.header("Inventory Spend")
    fig_inventory, _ = viz.display_per_transaction_type(TransactionType.INVENTORY)
    st.plotly_chart(fig_inventory)

    st.header("Profit")
    fig_profit, _ = viz.display_per_transaction_type(TransactionType.PROFIT)
    st.plotly_chart(fig_profit)

    st.header("Transactions")
    st.dataframe(cash_flow.dataframe())
    st.header("Amazon Payments")
    st.dataframe(df_payments)

    st.header("Files Visualizer")
    with st.form("files-viz"):
        transaction_id_ = st.text_input("Transaction ID")
        id_submited = st.form_submit_button("Show")
        
    break_ = 0
    if id_submited:
        for x in cash_flow.transactions:
            if x.id == int(transaction_id_):
                break_ = 1
                if x.file is not None:
                    for y in x.file:
                        st.image(base64_to_pil(y))
                else:
                    st.error("Transaction without documents.")

                break
            
        if break_ == 0:
            st.error("Transaction not detected.")
                

        




        




