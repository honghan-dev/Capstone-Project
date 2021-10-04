import streamlit as st
import pandas as pd
import plotly.express as px

header = st.beta_container()


@st.cache
def load_dataset_arr(df_arr, group_booking):
    df_arr["IL_STAUTC"] = pd.to_datetime(df_arr["IL_STAUTC"])
    df_arr["flighttouchdown_utc"] = pd.to_datetime(df_arr["flighttouchdown_utc"])
    df_arr["STA(LT)"] = df_arr["IL_STAUTC"] + pd.Timedelta(8, unit="hours")
    df_arr["Month"] = df_arr["STA(LT)"].dt.month_name()
    df_arr["Day"] = df_arr["STA(LT)"].dt.day_name()
    df_arr["Hour_of_day"] = df_arr["STA(LT)"].dt.hour
    df_arr["Int_count"] = df_arr["InternationalDesc"].apply(
        lambda x: 1 if x == "INT" else 0
    )
    df_arr["Dom_count"] = df_arr["InternationalDesc"].apply(
        lambda x: 0 if x == "INT" else 1
    )
    df_arr["Local"] = df_arr["BP_Nationality"].apply(lambda x: 1 if x == "MY" else 0)
    df_arr["Foreigner"] = df_arr["BP_Nationality"].apply(
        lambda x: 0 if x == "MY" else 1
    )
    df_arr["Counter"] = 1
    df_arr_booking = df_arr.groupby("BK_BookingID", as_index=False).count()
    if group_booking == 2:
        df_arr_filter = df_arr.drop_duplicates(subset="BK_BookingID")
    else:
        filter_booking = df_arr_booking[df_arr_booking["Counter"] < group_booking][
            "BK_BookingID"
        ]
        df_arr_filter = df_arr[df_arr["BK_BookingID"].isin(filter_booking)]
    return df_arr, df_arr_filter


@st.cache
def load_dataset_hotel(df_arr, df_hotel):
    df_hotel_filter = df_hotel[
        (df_hotel["country"] == "MALAYSIA")
        & (~df_hotel["hotel_name"].str.contains("TUNE"))
    ]
    df_arr_hotel = df_arr[
        df_arr["BC_EmailAddress"].isin(df_hotel_filter["HotelCust_Email"])
    ]
    df_arr_hotel = df_arr_hotel.drop_duplicates(subset="BK_BookingID")
    df_arr_hotel = df_arr_hotel.groupby("Hour_of_day", as_index=False).sum()
    return df_arr_hotel


@st.cache
def load_dataset_dep(df_arr, df_dep):
    df_dep = df_dep.drop_duplicates(subset="BK_BookingID")
    df_merge = pd.merge(df_arr, df_dep, on="BK_BookingID", how="left")
    df_merge["IL_STAUTC"] = pd.to_datetime(df_merge["IL_STAUTC"])
    df_merge["IL_STDUTC"] = pd.to_datetime(df_merge["IL_STDUTC"])
    df_merge["STA(LT)"] = df_merge["IL_STAUTC"] + pd.Timedelta(8, unit="hours")
    df_merge["STD(LT)"] = df_merge["IL_STDUTC"] + pd.Timedelta(8, unit="hours")
    df_merge["Hour"] = df_merge["STA(LT)"].dt.hour
    df_merge["Month"] = df_merge["STA(LT)"].dt.month_name()
    df_merge = df_merge[df_merge["IL_STDUTC"].notnull()]
    df_merge["Day_stay"] = (df_merge["STA(LT)"] - df_merge["STD(LT)"]).dt.days
    df_merge = df_merge[df_merge["Day_stay"] > 0]
    df_merge["more_equal_5"] = df_merge["Day_stay"].apply(lambda x: 1 if x >= 5 else 0)
    df_merge["less_5"] = df_merge["Day_stay"].apply(lambda x: 1 if x < 5 else 0)
    return df_merge


with header:
    st.sidebar.write("Please upload dataset")
    arr = st.sidebar.file_uploader("Upload Flight Arrival dataset")
    dep = st.sidebar.file_uploader("Upload Flight Departure dataset")
    snap = st.sidebar.file_uploader("Upload SNAP deal dataset")
    hotel = st.sidebar.file_uploader("Upload Hotel Booking dataset")

    st.image(
        "https://1000logos.net/wp-content/uploads/2020/04/AirAsia-Logo.png", width=120,
    )
    st.title("RBA CAPSTONE DATA ANALYSIS PROJECT")
    st.title("Demand for AirAsia Ride")
    st.write("<br>", unsafe_allow_html=True)
    # col1, col2 = st.beta_columns((2, 1))
    st.image(
        "https://harianpost.my/wp-content/uploads/2021/08/airasia-ride-04.jpg",
        width=800,
    )
    st.write("<br>", unsafe_allow_html=True)
    st.write(
        """<h2>Project Description""", unsafe_allow_html=True,
    )
    st.write("""Estimate ride-hailing demand from KLIA2 for AirAsia Ride""",)
    st.write("<br>", unsafe_allow_html=True)
    st.write("### Project objective")
    st.write(
        "Using passenger flight and hotel information to better understand the demand for Airasia Ride at KLIA 2."
    )
    st.write("<br><br>", unsafe_allow_html=True)
    if arr and dep and hotel and snap != None:
        df_arr = pd.read_csv(arr)
        df_dep = pd.read_csv(dep)
        df_snap = pd.read_csv(snap)
        df_hotel = pd.read_csv(hotel)

        st.dataframe(df_arr)
        group_booking = st.slider(
            """Slide along to filter out bookings with bigger number of passenger in the same booking.
            Minimum value indicates that the dataset only includes booking numbers which are unique""",
            min_value=2,
            max_value=60,
            step=2,
        )
        df_arr, df_arr_filter = load_dataset_arr(df_arr, group_booking)
        # Loading dataset

        st.write("## Data Visualisation")

        # By the hour
        st.write(
            """<h3 style:'text-align:center'>Total number of passenger arrival every hour in a day""",
            unsafe_allow_html=True,
        )

        df_arr_hour = df_arr_filter.groupby("Hour_of_day", as_index=False).sum()
        fig_hour = px.bar(
            df_arr_hour,
            x="Hour_of_day",
            y="Counter",
            barmode="group",
            text="Counter",
            labels={"Counter": "No. of Pax", "Hour_of_day": "Hour of Day"},
        )
        fig_hour.update_traces(texttemplate="%{text:.3s}", textposition="outside")
        fig_hour.update_layout(uniformtext_minsize=10)
        st.write(f"Total of {df_arr_hour['Counter'].sum()} passenger in this dataset")
        st.plotly_chart(fig_hour)

        st.write(
            """<h3 style:'text-align:center'>Total number of passenger arrival in each hour of the day separated by Local or Foreigner""",
            unsafe_allow_html=True,
        )
        fig_local = px.bar(
            df_arr_hour,
            x="Hour_of_day",
            y=["Local", "Foreigner"],
            labels={"value": "No of Pax"},
            barmode="group",
        )
        st.write(f"Total of {df_arr_hour['Counter'].sum()} passenger in this dataset")
        st.plotly_chart(fig_local)

        # By Day and Hour
        st.write(
            """<h3 style:'text-align:center'>Number of arrivals in a week aggregated by Passenger Nationality (Local or Foreigner)""",
            unsafe_allow_html=True,
        )
        option = ["Combined", "Separate"]
        choice = st.radio("Change the layout of the chart", option, key="1")
        df_arr_day = df_arr_filter.groupby(["Day", "Hour_of_day"], as_index=False).sum()
        st.write(f"Total of {df_arr_day['Counter'].sum()} passenger in this dataset")
        if choice == "Separate":
            fig_day = px.bar(
                df_arr_day,
                x="Hour_of_day",
                y=["Local", "Foreigner"],
                labels={"value": "No of Pax"},
                barmode="group",
                facet_col="Day",
                facet_col_wrap=3,
                width=800,
                category_orders={
                    "Day": [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday",
                    ]
                },
            )
            fig_day.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_day)
        else:
            fig_day = px.bar(
                df_arr_day,
                x="Day",
                y="Counter",
                labels={"Counter": "No of Pax"},
                barmode="group",
                color="Hour_of_day",
                color_continuous_scale=px.colors.diverging.RdBu,
                category_orders={
                    "Day": [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday",
                    ]
                },
            )
            fig_day.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_day)

        # By Month and hour
        choose = ["Combined", "Separate"]
        choice_2 = st.radio("Change the layout of the chart", choose, key="2")
        st.write(
            """<h3 style:'text-align:center'>Number of arrivals in a month aggregated by Passenger Nationality (Local or Foreigner)""",
            unsafe_allow_html=True,
        )
        df_arr_month = df_arr_filter.groupby(
            ["Month", "Day", "Hour_of_day"], as_index=False
        ).sum()
        st.write(f"Total of {df_arr_month['Counter'].sum()} passenger in this dataset")
        if choice_2 == "Separate":
            fig_month = px.bar(
                df_arr_month,
                x="Hour_of_day",
                y=["Local", "Foreigner"],
                labels={"value": "No of Pax"},
                barmode="group",
                facet_col="Month",
                facet_col_wrap=3,
                width=800,
                category_orders={
                    "Month": [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                    ]
                },
            )
            fig_month.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_month)
        else:
            fig_month = px.bar(
                df_arr_month,
                x="Month",
                y="Counter",
                labels={"Counter": "No of Pax"},
                category_orders={
                    "Month": [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                    ]
                },
            )
            fig_month.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_month)

        st.write(
            """<h3 style:'text-align:center'>The number of arrivals each hour in a month categorised by trip length of less than 5 days and 5 days or more.""",
            unsafe_allow_html=True,
        )

        df_merge = load_dataset_dep(df_arr, df_dep)
        df_merge = df_merge.groupby(["Month", "Hour"], as_index=False).sum()
        st.write(f"Total of {df_merge['Counter'].sum()} passenger in this dataset")
        fig_day_stay = px.bar(
            df_merge,
            x="Hour",
            y=["less_5", "more_equal_5"],
            facet_col="Month",
            facet_col_wrap=3,
            width=800,
            category_orders={
                "Month": [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                ]
            },
        )
        st.plotly_chart(fig_day_stay)

        st.write(
            """<h3 style:'text-align:center'>Number of arrivals which have already booked a hotel other than hotel located in Sepang""",
            unsafe_allow_html=True,
        )
        df_arr_hotel = load_dataset_hotel(df_arr, df_hotel)
        st.write(f"Total of {df_arr_hotel['Counter'].sum()} passenger in this dataset")
        fig_arr_hotel = px.bar(
            df_arr_hotel,
            x="Hour_of_day",
            y=["Local", "Foreigner"],
            labels={"value": "No of Pax"},
            barmode="group",
        )
        st.plotly_chart(fig_arr_hotel)
        st.write(
            """1200HR has the highest number of arrival for passengers who
            have booked both flight and hotel in the same booking."""
        )

