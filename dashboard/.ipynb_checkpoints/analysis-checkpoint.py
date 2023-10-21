import soap_dispenser_set

FULFILLMENT_FEE = 6.39
INITIAL_UNITS = 504

package = soap_dispenser_set.Package(
    width=20.5,
    lenght=26.2,
    height=12.3,
    weight=1.21,
    cost=1.7,
)

box = soap_dispenser_set.Box(
    width=52,
    lenght=29,
    height=45,
    weight=9.98,
    number_packages=6,
    package=package,
)

results = []
for price in range(30, 40, 3):
    AMAZON_FEE = 0.15*price + 0.99
    fees = soap_dispenser_set.Fees(
        amazon_fee=AMAZON_FEE,
        fulfillment_fee=FULFILLMENT_FEE,
    )
    product = soap_dispenser_set.SoapDispenserSet(
        price=price,
        exw_cost=(1.84*2)+(0.14*3)+(0.08*3)+0.02+3.3+0.1,
        package=package,
        box=box,
        shipment_cost=2.34,
        fees=fees,
    )
    for daily_sales in (3, 5, 8, 12, 15):
        for ppc_percentage in (0.2, 0.1, 0.0):
            profit_margin = product.estimate_profit_margin(
                initial_units_stored=INITIAL_UNITS,
                average_daily_units_sold=daily_sales,
                percentage_on_ppc=ppc_percentage,
            )
            results.append(
                {
                    "variables":{
                        "price":price,
                        "daily_sales":daily_sales,
                        "ppc_percentage":ppc_percentage,
                    },
                    "results":{
                        "profit_margin":profit_margin,
                        "unit_profit":profit_margin*price,
                        "monthly_profit":profit_margin*price*daily_sales*30.5
                    }
                }
            )

print(results)