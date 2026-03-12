import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="IT Lab Stock Management", layout="wide")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("inventory.db", check_same_thread=False)
c = conn.cursor()

# ---------------- TABLES ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS systems(
system_no INTEGER PRIMARY KEY,
name TEXT,
category TEXT,
quantity INTEGER,
quality TEXT,
status TEXT,
purchase_date TEXT,
warranty_year INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
role TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS complaints(
id INTEGER PRIMARY KEY AUTOINCREMENT,
raised_by TEXT,
title TEXT,
description TEXT,
status TEXT,
date_time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS dead_stock(
id INTEGER PRIMARY KEY AUTOINCREMENT,
system_no INTEGER,
name TEXT,
reason TEXT,
accepted_by TEXT,
date_time TEXT
)
""")

conn.commit()

# ---------------- DEFAULT USERS ----------------
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    users = [
        ("admin","admin123","Admin"),
        ("hod","hod123","HOD"),
        ("principal","principal123","Principal")
    ]
    c.executemany("INSERT INTO users VALUES(?,?,?)",users)
    conn.commit()

# ---------------- SESSION ----------------
if "logged" not in st.session_state:
    st.session_state.logged=False
if "role" not in st.session_state:
    st.session_state.role=""
if "username" not in st.session_state:
    st.session_state.username=""

# ---------------- HELPERS ----------------
def now():
    return datetime.now().strftime("%d-%m-%Y %H:%M")

def next_system():
    c.execute("SELECT MAX(system_no) FROM systems")
    r=c.fetchone()[0]
    return 2000 if r is None else r+1

# ---------------- LOGIN ----------------
def login():

    st.title("IT Lab Login")

    u=st.text_input("Username")
    p=st.text_input("Password",type="password")

    if st.button("Login"):

        c.execute("SELECT role FROM users WHERE username=? AND password=?",(u,p))
        r=c.fetchone()

        if r:
            st.session_state.logged=True
            st.session_state.role=r[0]
            st.session_state.username=u
            st.success("Login Success")
            st.rerun()

        else:
            st.error("Invalid Login")

# ---------------- MAIN ----------------
def main():

    role=st.session_state.role
    st.title("IT Lab Stock Management")

    if st.sidebar.button("Logout"):
        st.session_state.logged=False
        st.rerun()

# ---------------- MENU ----------------
    if role=="Admin":

        menu=[
        "Dashboard",
        "Register",
        "Add Item",
        "Update Item",
        "Delete Item",
        "Users",
        "Complaints",
        "Dead Stock",
        "Reports"
        ]

    else:

        menu=[
        "Dashboard",
        "Register",
        "Raise Complaint",
        "Dead Stock",
        "Reports"
        ]

    choice=st.sidebar.selectbox("Menu",menu)

# ---------------- DASHBOARD ----------------
    if choice=="Dashboard":

        df=pd.read_sql("SELECT * FROM systems",conn)

        col1,col2,col3=st.columns(3)

        col1.metric("Total Items",len(df))
        col2.metric("Total Quantity",df["quantity"].sum() if not df.empty else 0)
        col3.metric("Not Working",len(df[df.status=="Not Working"]) if not df.empty else 0)

# ---------------- REGISTER ----------------
    elif choice=="Register":

        st.subheader("Items Register")

        df=pd.read_sql("SELECT * FROM systems",conn)

        search=st.text_input("Search Item")

        if search:
            df=df[df["name"].str.contains(search,case=False)]

        st.dataframe(df,use_container_width=True)

# ---------------- ADD ITEM ----------------
    elif choice=="Add Item":

        st.subheader("Add Item")

        sys=next_system()

        name=st.text_input("Item Name")
        category=st.selectbox("Category",["Input","Output","Networking","Storage"])
        qty=st.number_input("Quantity",0)
        quality=st.selectbox("Quality",["Good","Average","Poor"])
        status=st.selectbox("Status",["Working","Not Working"])
        purchase=st.date_input("Purchase Date")
        warranty=st.number_input("Warranty Years",0)

        if st.button("Add"):

            c.execute("""
            INSERT INTO systems VALUES(?,?,?,?,?,?,?,?)
            """,(sys,name,category,qty,quality,status,str(purchase),warranty))

            conn.commit()
            st.success("Item Added")
            st.rerun()

# ---------------- UPDATE ----------------
    elif choice=="Update Item":

        sys=st.number_input("System No",2000)

        c.execute("SELECT * FROM systems WHERE system_no=?",(sys,))
        r=c.fetchone()

        if r:

            name=st.text_input("Name",r[1])
            qty=st.number_input("Quantity",0,value=r[3])

            if st.button("Update"):

                c.execute("""
                UPDATE systems
                SET name=?,quantity=?
                WHERE system_no=?
                """,(name,qty,sys))

                conn.commit()
                st.success("Updated")
                st.rerun()

        else:

            st.info("Item Not Found")

# ---------------- DELETE ----------------
    elif choice=="Delete Item":

        sys=st.number_input("System No",2000)

        if st.button("Delete"):

            c.execute("DELETE FROM systems WHERE system_no=?",(sys,))
            conn.commit()
            st.success("Deleted")
            st.rerun()

# ---------------- USERS ----------------
    elif choice=="Users":

        st.subheader("User Management")

        u=st.text_input("Username")
        p=st.text_input("Password")
        r=st.selectbox("Role",["Admin","HOD","Principal"])

        if st.button("Add User"):

            c.execute("INSERT INTO users VALUES(?,?,?)",(u,p,r))
            conn.commit()
            st.success("User Added")

        df=pd.read_sql("SELECT * FROM users",conn)
        st.dataframe(df)

# ---------------- COMPLAINT ----------------
    elif choice=="Raise Complaint":

        title=st.text_input("Title")
        desc=st.text_area("Description")

        if st.button("Submit"):

            c.execute("""
            INSERT INTO complaints
            (raised_by,title,description,status,date_time)
            VALUES(?,?,?,?,?)
            """,(st.session_state.username,title,desc,"Open",now()))

            conn.commit()
            st.success("Complaint Sent")

# ---------------- ADMIN COMPLAINT ----------------
    elif choice=="Complaints":

        df=pd.read_sql("SELECT * FROM complaints",conn)

        st.dataframe(df)

# ---------------- DEAD STOCK ----------------
    elif choice=="Dead Stock":

        df=pd.read_sql("SELECT * FROM systems",conn)

        sys=st.selectbox("System",df["system_no"])

        reason=st.text_input("Reason")

        if st.button("Move"):

            name=df[df.system_no==sys].iloc[0]["name"]

            c.execute("""
            INSERT INTO dead_stock
            (system_no,name,reason,accepted_by,date_time)
            VALUES(?,?,?,?,?)
            """,(sys,name,reason,st.session_state.username,now()))

            c.execute("DELETE FROM systems WHERE system_no=?",(sys,))

            conn.commit()
            st.success("Moved")

        ds=pd.read_sql("SELECT * FROM dead_stock",conn)

        st.dataframe(ds)

# ---------------- REPORT ----------------
    elif choice=="Reports":

        df=pd.read_sql("SELECT * FROM systems",conn)

        st.bar_chart(df.set_index("name")["quantity"])

        fig,ax=plt.subplots()

        ax.pie(
        df["status"].value_counts(),
        labels=df["status"].value_counts().index,
        autopct="%1.1f%%"
        )

        st.pyplot(fig)

# ---------------- RUN ----------------
if not st.session_state.logged:
    login()
else:
    main()
