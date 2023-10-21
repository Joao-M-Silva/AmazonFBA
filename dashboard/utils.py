from pathlib import Path
from typing import Union, List
import json
import streamlit as st
from products.utils import Month, Package, Box, Fees, StockFlow, Product


def load_products(path: Union[str, Path]) -> List[Product]:
    """
    Load the products stored in a .json file
    """
    with open(path, "r") as f:
        products_data : List[dict] = json.load(f)
    
    return [
        Product(
            name=product["name"],
            price_before_discount=product["price_before_discount"],
            discount=product["discount"],
            exw_cost=product["exw_cost"],
            package=Package(**product["package"]),
            shipment_cost=product["shipment_cost"],
            fees=Fees(**product["fees"]),
            image=product["image"],
        )
        for product in products_data
    ]


def dump_products(products: List[Product], path: Union[str, Path]):
    """
    Dump products list into a .json file
    """
    products_data = [
        product.json()
        for product in products
    ]
    with open(path, "w") as f:
        json.dump(products_data, f)


def load_performance_data(path: Union[str, Path]) -> List[dict]:
    """
    Load the performance data stored in a .json file
    """
    with open(path, "r") as f:
        data : List[dict] = json.load(f)
    
    return data


def dump_performance_data(data: List[dict], path: Union[str, Path]):
    """
    Dump performance data into a .json file
    """
    with open(path, "w") as f:
        json.dump(data, f)


def instantiate_product(product :Product = None) -> Product:
    # Instantiate a Package
    with st.form("package-instantiation"):
        st.subheader("Package")
        package = Package(
            width=st.number_input(
                "Width", 
                value=product.package.width if product else 0.0,
            ),
            lenght=st.number_input(
                "Length", 
                value=product.package.lenght if product else 0.0,
            ),
            height=st.number_input(
                "Height",
                value=product.package.height if product else 0.0,
            ),
            weight=st.number_input(
                "Weight",
                value=product.package.weight if product else 0.0,
            ),
            cost=st.number_input(
                "Cost",
                value=product.package.cost if product else 0.0,
            )
        )
        st.write("***")
        st.subheader("Fees")
        fees = Fees(
            amazon_fee=st.number_input(
                "Amazon Fee",
                value=product.fees.amazon_fee if product else 0.0,
            ),
            fulfillment_fee=st.number_input(
                "Fulfillment Fee",
                value=product.fees.fulfillment_fee if product else 0.0,
            )
        )
        st.write("***")
        st.subheader("Product")
        product = Product(
            name=st.text_input(
                "Name",
                value=product.name if product else "",
            ),
            price_before_discount=st.number_input(
                "Price Before Discount",
                value=product.price_before_discount if product else 0.0,
            ),
            discount=st.number_input(
                "Discount", 
                min_value=0.0, 
                max_value=1.0,
                value=product.discount if product else 0.0,
            ),
            exw_cost=st.number_input(
                "EXW Cost",
                value=product.exw_cost if product else 0.0,
            ),
            package=package,
            shipment_cost=st.number_input(
                "Shipping Cost",
                value=product.shipment_cost if product else 0.0,
            ),
            fees=fees,
            image=None,
        )

        submit_button = st.form_submit_button("Create")
    
    if submit_button:
        product.fees.validate_amazon_fee(product.price_before_discount * (1 - product.discount))
        return product
    else:
        return None
    

def product_display(product: Product):
    st.header("Product Selected: ")
    st.subheader(product.name)
    st.write("- Price Before Discount: ", product.price_before_discount)
    st.write("- Discount: ", product.discount)
    st.write("- Price: ", product.price)
    st.write("- EXW Cost: ", product.exw_cost)
    st.write("- Shipping Cost: ", product.shipment_cost)
    st.write("***")
    st.subheader("Package:")
    st.write("- Width: ", product.package.width)
    st.write("- Lenght: ", product.package.lenght)
    st.write("- Height: ", product.package.weight)
    st.write("- Weight: ", product.package.weight)
    st.write("- Cost: ", product.package.cost)
    st.write("***")
    st.subheader("Fees:")
    st.write("- Amazon Fee: ", product.fees.amazon_fee)
    st.write("- Fulfillment Fee: ", product.fees.fulfillment_fee)
    st.write("***")
    st.subheader("Profit & Margins:")
    st.write("- Profit: ", product.profit())
    st.write("- Profit Margin: ", product.profit_margin())
    st.write("- Amazon Payment: ", product.amazon_payment)
    st.write("- ROI: ", product.ROI())
    st.write("***")
   