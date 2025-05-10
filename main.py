import os
import uuid
import streamlit as st
import psycopg2
from datetime import date, timedelta

# ——— Database connection ———
DB_HOST     = os.getenv('DB_HOST', 'localhost')
DB_PORT     = os.getenv('DB_PORT', '5432')  # Adjust port if needed
DB_NAME     = os.getenv('DB_NAME', 'DBOSchema')
DB_USER     = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'tgms1402')

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# ——— Page implementations ———

def signup_page():
    st.title('Sign Up')
    role    = st.selectbox('Sign up as', ['Renter', 'Agent'])
    email   = st.text_input('Email')
    name    = st.text_input('Name')
    address = st.text_input('Address')
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Sign Up'):
            if not email:
                st.error('Enter an email')
                return
            conn = get_connection(); cur = conn.cursor()
            cur.execute(
                "INSERT INTO Users(Name_, address, Email, UserType) VALUES (%s, %s, %s, %s) ON CONFLICT (Email) DO NOTHING",
                (name, address, email, role)
            )
            new_id = uuid.uuid4().hex[:8]
            if role == 'Renter':
                cur.execute(
                    "INSERT INTO Renter(RenterID, Email) VALUES (%s, %s) ON CONFLICT (RenterID) DO NOTHING",
                    (new_id, email)
                )
            else:
                cur.execute(
                    "INSERT INTO Agent(AgentID, Email) VALUES (%s, %s) ON CONFLICT (AgentID) DO NOTHING",
                    (new_id, email)
                )
            conn.commit(); cur.close(); conn.close()
            st.success(f'Signed up! Your {role} ID is {new_id}')
            st.session_state.page = 'login'; st.rerun()
    with col2:
        if st.button('Go to Login'):
            st.session_state.page = 'login'; st.rerun()


def login_page():
    st.title('Login')
    email = st.text_input('Email')
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Login'):
            conn = get_connection(); cur = conn.cursor()
            cur.execute("SELECT UserType FROM Users WHERE Email = %s", (email,))
            row = cur.fetchone(); cur.close(); conn.close()
            if row:
                st.session_state.email = email; st.session_state.role = row[0]
                st.success(f"Logged in as {row[0]}")
                st.session_state.page = ('add' if row[0] == 'Agent' else 'view')
                st.rerun()
            else:
                st.error('No such user')
    with col2:
        if st.button('Go to Sign Up'):
            st.session_state.page = 'signup'; st.rerun()


def profile_page():
    st.header('Your Profile')
    current_email = st.session_state.get('email')

    conn, cur = get_connection(), get_connection().cursor()
    cur.execute("SELECT Name_, address, UserType FROM Users WHERE Email = %s", (current_email,))
    name, addr, role = cur.fetchone() or ('', '', '')

    st.subheader('Account Details')
    new_email = st.text_input("Email",   value=current_email)
    new_addr  = st.text_input("Address", value=addr)

    if st.button('Save Changes'):
        if new_email and new_addr:
            # Update child table first if email changed
            if new_email != current_email:
                if role == 'Renter':
                    cur.execute("UPDATE Renter  SET Email = %s WHERE Email = %s",
                                (new_email, current_email))
                else:
                    cur.execute("UPDATE Agent   SET Email = %s WHERE Email = %s",
                                (new_email, current_email))
            # Then update Users table
            cur.execute(
                "UPDATE Users SET Email = %s, address = %s WHERE Email = %s",
                (new_email, new_addr, current_email)
            )
            conn.commit()
            st.session_state.email = new_email
            st.success('Profile updated!')
            st.rerun()
        else:
            st.error('Email and Address cannot be empty')

    st.write(f"**Name:** {name}")
    st.write(f"**Role:** {role}")

    # Renter-specific details
    if role == 'Renter':
        # Fetch RenterID
        cur.execute("SELECT RenterID FROM Renter WHERE Email = %s", (st.session_state['email'],))
        renter = cur.fetchone()
        if renter:
            r_id = renter[0]
            st.write(f"**Renter ID:** {r_id}")
            cur.execute("SELECT Reward_Points FROM Rewards WHERE R_id = %s", (r_id,))
            pts = cur.fetchone(); pts = pts[0] if pts else 0
            st.write(f"**Reward Points:** {pts}")
            st.subheader('Your Bookings')
            # fetch all bookings + property type and ID
            cur.execute("""
                SELECT
                  b.BookID,
                  b.PropId,
                  p.PropType,
                  b.StartDate,
                  b.EndDate,
                  b.Mode_of_pay,
                  b.TotalCost
                FROM Booking b
                JOIN Property p ON b.PropId = p.PropId
                WHERE b.RenterID = %s
            """, (r_id,))
            bookings = cur.fetchall()

            if bookings:
                for book_id, prop_id, prop_type, start, end, mode, cost in bookings:
                    st.write(f"• **{book_id}**: {prop_type} ({prop_id}), {start}–{end}, {mode}, **${cost:.2f}**")
                    # receipt button
                    if st.button("Show Receipt", key=f"receipt_{book_id}"):
                        st.markdown("#### Receipt Details")
                        st.write(f"**Booking ID:** {book_id}")
                        st.write(f"**Property ID:** {prop_id}")
                        st.write(f"**Property Type:** {prop_type}")
                        st.write(f"**Period:** {start} → {end}")
                        st.write(f"**Payment Mode:** {mode}")
                        st.write(f"**Total Cost:** ${cost:.2f}")
                        st.write("---")
            else:
                st.write("No bookings yet")
        else:
            st.warning('No renter record found for this email')

    cur.close(); conn.close()
    if st.button('Back'):
        st.session_state.page = 'view'; st.rerun()


def view_page():
    st.header('Available Properties')
    search_id = st.text_input('Search by Property ID')

    conn = get_connection()
    cur = conn.cursor()

    # 1) Fetch matching properties
    if search_id:
        cur.execute(
            "SELECT PropId, PropType, Description, City, State_ "
            "FROM Property WHERE PropId = %s",
            (search_id,)
        )
    else:
        cur.execute(
            "SELECT PropId, PropType, Description, City, State_ "
            "FROM Property"
        )
    props = cur.fetchall()
    if search_id and not props:
        st.warning(f"No property found with ID {search_id}")

    # 2) Get current agent’s ID
    agent_id = None
    if st.session_state.role == 'Agent':
        cur.execute("SELECT AgentID FROM Agent WHERE Email = %s",
                    (st.session_state.email,))
        row = cur.fetchone()
        agent_id = row[0] if row else None

    type_map = {
        'VacHome':      ('VacHome',      'VacHomeId'),
        'Houses':       ('Houses',       'HouseId'),
        'Apartments':   ('Apartments',   'AptId'),
        'CommBuildings':('CommBuildings','BuildId'),
    }

    for pid, ptype, desc, city, state in props:
        table, col = type_map[ptype]

        # a) price & availability
        cur.execute(
            f"SELECT Price, Availablity FROM {table} WHERE {col} = %s",
            (pid,)
        )
        price, available = cur.fetchone()

        # b) who added it
        cur.execute(
            "SELECT u.Name_, a.AgentID "
            "FROM Property p "
            " JOIN Agent a ON p.AgentID = a.AgentID "
            " JOIN Users u ON a.Email = u.Email "
            "WHERE p.PropId = %s",
            (pid,)
        )
        owner = cur.fetchone()
        if owner:
            added_by_name, added_by_id = owner
        else:
            added_by_name, added_by_id = "Unknown", None

        # c) display
        st.subheader(f"{pid}: {ptype} in {city}, {state}")
        st.write(f"**Description:** {desc}")
        st.write(f"**Price:** ${price:.2f}")
        st.write(f"**Available:** {'✅' if available else '❌'}")
        st.write(f"**Added by:** {added_by_name}"
                 + (f" (Agent ID: {added_by_id})" if added_by_id else ""))

        # d) Renters can buy
        if st.session_state.role == 'Renter' and available:
            if st.button(f"Buy {pid}", key=f"buy_{pid}"):
                st.session_state.selected_prop = pid
                st.session_state.page = 'buy'
                st.rerun()
                return  # let Streamlit rerun

        # e) Agents can edit/delete their own listings
        if st.session_state.role == 'Agent' and added_by_id == agent_id:
            edit_col, del_col = st.columns(2)
            with edit_col:
                if st.button("Edit", key=f"edit_{pid}"):
                    st.session_state.edit_prop = pid
                    st.session_state.page = 'edit'
                    st.rerun()
                    return
            with del_col:
                if st.button("Delete", key=f"del_{pid}"):
                    # delete child rows first
                    cur.execute(f"DELETE FROM {table} WHERE {col} = %s", (pid,))
                    cur.execute("DELETE FROM Neighbourhood WHERE PropId = %s", (pid,))
                    cur.execute("DELETE FROM Property WHERE PropId = %s",   (pid,))
                    conn.commit()
                    st.success("Property deleted.")
                    st.rerun()
                    return

    # Agents can also add new
    if st.session_state.role == 'Agent' and st.button('Add Property'):
        st.session_state.page = 'add'
        st.rerun()
        return

    # navigation
    c1, c2 = st.columns(2)
    with c1:
        if st.button('Profile'):
            st.session_state.page = 'profile'
            st.rerun()
            return
    with c2:
        if st.button('Logout'):
            st.session_state.page = 'login'
            st.rerun()
            return

    cur.close()
    conn.close()


def edit_page():
    pid = st.session_state.get('edit_prop')
    if not pid:
        st.error("No property selected to edit.")
        return

    conn = get_connection()
    cur = conn.cursor()

    # 1) Load from Property
    cur.execute(
        "SELECT PropType, Description, City, State_ FROM Property WHERE PropId = %s",
        (pid,)
    )
    ptype, desc, city, state = cur.fetchone()

    # 2) Load from subtype table
    type_map = {
        'VacHome':      ('VacHome',      'VacHomeId'),
        'Houses':       ('Houses',       'HouseId'),
        'Apartments':   ('Apartments',   'AptId'),
        'CommBuildings':('CommBuildings','BuildId'),
    }
    table, col = type_map[ptype]
    cur.execute(
        f"SELECT * FROM {table} WHERE {col} = %s",
        (pid,)
    )
    # columns are [id, NoOfRooms?, address?, SqFootage?, Price?, Availablity?, …maybe BuildingType]
    subtype_row = cur.fetchone()

    # 3) Load neighbourhood
    cur.execute(
      "SELECT CrimeRate, NearbySchool, Hospital, Park, mart "
      "FROM Neighbourhood WHERE PropId = %s",
      (pid,)
    )
    n_row = cur.fetchone()

    # 4) Show form
    st.header(f"Edit {ptype} {pid}")
    new_desc  = st.text_input("Description", value=desc)
    new_city  = st.text_input("City", value=city)
    new_state = st.text_input("State", value=state)

    # subtype fields
    if ptype in ('VacHome','Houses','Apartments'):
        _, rooms, addr, sqft, price, avail, *rest = subtype_row
        rooms = int(rooms)
        sqft = float(sqft)
        price = float(price)
        new_rooms = st.number_input(
            "No of Rooms",
            min_value=1,
            value=rooms  # now an int
        )
        new_addr = st.text_input("Address", value=addr)
        new_sqft = st.number_input(
            "SqFootage",
            min_value=0.0,
            value=sqft,  # now a float
            format="%.2f"
        )
        new_price = st.number_input(
            "Price",
            min_value=0.0,
            value=price,  # now a float
            format="%.2f"
        )
        new_avail = st.checkbox("Available", value=avail)
        if ptype == 'Apartments':
            building_type = rest[0]
            new_btype = st.text_input("BuildingType", value=building_type)
    else:  # CommBuildings
        _, addr, btype, sqft, price, avail = subtype_row
        new_addr  = st.text_input("Address", value=addr)
        new_btype = st.text_input("BusinessType", value=btype)
        new_sqft  = st.number_input("SqFootage", value=float(sqft))
        new_price = st.number_input("Price", value=float(price))
        new_avail = st.checkbox("Available", value=avail)

    # neighbourhood fields
    crime, school, hosp, park, mart = n_row
    new_crime  = st.number_input('Crime Rate (0–99.99)', min_value=0.0, max_value=99.99, value=float(crime), format="%.2f")
    new_school = st.text_input('Nearby School', value=school)
    new_hosp   = st.text_input('Nearest Hospital', value=hosp)
    new_park   = st.text_input('Closest Park', value=park)
    new_mart   = st.text_input('Nearby Mart', value=mart)

    if st.button("Save Changes"):
        # a) update Property
        cur.execute(
            "UPDATE Property SET Description=%s, City=%s, State_=%s WHERE PropId=%s",
            (new_desc, new_city, new_state, pid)
        )

        # b) update subtype
        if ptype in ('VacHome','Houses','Apartments'):
            cols = "(NoOfRooms, address, SqFootage, Price, Availablity" + (", BuildingType)" if ptype=='Apartments' else ")")
            vals = [new_rooms, new_addr, new_sqft, new_price, new_avail]
            if ptype == 'Apartments': vals.append(new_btype)
            cur.execute(
                f"UPDATE {table} SET NoOfRooms=%s, address=%s, SqFootage=%s, Price=%s, Availablity=%s"
                + (", BuildingType=%s" if ptype=='Apartments' else "")
                + f" WHERE {col}=%s",
                (*vals, pid)
            )
        else:
            cur.execute(
                f"UPDATE CommBuildings SET address=%s, BusinessType=%s, SqFootage=%s, Price=%s, Availablity=%s WHERE BuildId=%s",
                (new_addr, new_btype, new_sqft, new_price, new_avail, pid)
            )

        # c) update neighbourhood
        cur.execute(
            "UPDATE Neighbourhood SET CrimeRate=%s, NearbySchool=%s, Hospital=%s, Park=%s, mart=%s WHERE PropId=%s",
            (new_crime, new_school, new_hosp, new_park, new_mart, pid)
        )

        conn.commit()
        st.success("Property updated!")
        st.session_state.page = 'view'
        st.rerun()
        return

    if st.button("Cancel"):
        st.session_state.page = 'view'
        st.rerun()
        return

    cur.close()
    conn.close()




def buy_page():
    st.header('Buy Property')
    default_prop = st.session_state.get('selected_prop', '')
    prop_id       = st.text_input('Property ID to buy', value=default_prop)
    mode_of_pay   = st.selectbox('Mode of Pay', ['Cash', 'Credit'])
    if mode_of_pay == 'Credit':
        card_name = st.text_input('Card Holder Name')
        card_no   = st.text_input('Card Number')
        exp_date  = st.date_input('Expiry Date')
        cvv       = st.text_input('CVV')

    if st.button('Confirm Purchase'):
        # 1) Basic props check
        if not prop_id:
            st.error("Enter a property ID")
            return

        # 2) If credit, validate 16-digit numeric card number
        if mode_of_pay == 'Credit':
            if not card_no.isdigit() or len(card_no) != 16:
                st.error("Credit card number must be exactly 16 digits")
                return
            # (you could also validate CVV length here, etc.)

        # 3) Proceed with booking
        conn = get_connection(); cur = conn.cursor()
        booking_id = uuid.uuid4().hex[:10]
        cur.execute("SELECT RenterID FROM Renter WHERE Email = %s",
                    (st.session_state['email'],))
        r_id = cur.fetchone()[0]

        cur.execute("SELECT PropType FROM Property WHERE PropId = %s",
                    (prop_id,))
        ptype = cur.fetchone()[0]
        table, col = {
            'VacHome':     ('VacHome',    'VacHomeId'),
            'Houses':      ('Houses',     'HouseId'),
            'Apartments':  ('Apartments', 'AptId'),
            'CommBuildings':('CommBuildings','BuildId'),
        }[ptype]

        cur.execute(f"SELECT Price FROM {table} WHERE {col} = %s",
                    (prop_id,))
        total_cost = cur.fetchone()[0]

        start_date = date.today()
        end_date   = start_date + timedelta(days=30)

        cur.execute(
            """
            INSERT INTO Booking
              (RenterID, BookID, PropId, StartDate, EndDate, Mode_of_pay, TotalCost)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (r_id, booking_id, prop_id, start_date, end_date, mode_of_pay, total_cost)
        )
        cur.execute(
            f"UPDATE {table} SET Availablity = FALSE WHERE {col} = %s",
            (prop_id,)
        )

        if mode_of_pay == 'Credit':
            cur.execute(
                "INSERT INTO CreditCard(RenterID, Card_name, Card_no, exp_date, cvv) "
                "VALUES (%s, %s, %s, %s, %s)",
                (r_id, card_name, card_no, exp_date, cvv)
            )

        cur.execute(
            "INSERT INTO Rewards(R_id, Reward_Points) VALUES (%s, 100) "
            "ON CONFLICT (R_id) DO UPDATE "
            "  SET Reward_Points = Rewards.Reward_Points + 100",
            (r_id,)
        )

        conn.commit()
        cur.close()
        conn.close()

        st.session_state.receipt = {
            'booking_id': booking_id,
            'prop_id':    prop_id,
            'mode':       mode_of_pay,
            'total':      total_cost,
            'start':      start_date,
            'end':        end_date,
            'card_name':  locals().get('card_name',''),
            'card_no':    locals().get('card_no','')
        }
        st.session_state.page = 'profile'
        st.rerun()



def add_page():
    st.header('Add Property')
    if st.button('View Properties'): st.session_state.page='view'; st.rerun()
    type_        = st.selectbox('Type', ['VacHome', 'Houses', 'Apartments','CommBuildings'])
    description  = st.text_input('Description')
    city         = st.text_input('City'); state = st.text_input('State')
    if type_ in ['VacHome','Houses','Apartments']:
        rooms=st.number_input('No of Rooms',1,100); addr=st.text_input('Address')
        sqft=st.number_input('SqFootage',0.0); price=st.number_input('Price',0.0)
        availability=st.checkbox('Available',True)
        if type_=='Apartments': btype=st.text_input('BuildingType')
    else:
        addr=st.text_input('Address'); btype=st.text_input('BusinessType')
        sqft=st.number_input('SqFootage',0.0); price=st.number_input('Price',0.0)
        availability=st.checkbox('Available',True)
    st.markdown("#### Neighbourhood Details")
    crime_rate=st.number_input('Crime Rate (0.00–99.99)',min_value=0.00,max_value=99.99,format="%.2f")
    nearby_school=st.text_input('Nearby School')
    hospital=st.text_input('Nearest Hospital')
    park=st.text_input('Closest Park')
    mart=st.text_input('Nearby Mart')
    if st.button('Add Property'):
        conn=get_connection(); cur=conn.cursor()
        cur.execute("SELECT MAX(CAST(PropId AS bigint)) FROM Property")
        max_id=cur.fetchone()[0] or 0; prop_id=str(int(max_id)+1).zfill(10)
        # inside add_page(), before inserting into Property
        cur.execute("SELECT AgentID FROM Agent WHERE Email = %s",
                    (st.session_state.email,))
        agent_id = cur.fetchone()[0]
        # now include AgentID in the insert:
        cur.execute(
            "INSERT INTO Property(PropId, PropType, Description, City, State_, AgentID) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (prop_id, type_, description, city, state, agent_id)
        )
        if type_=='VacHome': cur.execute("INSERT INTO VacHome VALUES(%s,%s,%s,%s,%s,%s)",(prop_id,rooms,addr,sqft,price,availability))
        elif type_=='Houses': cur.execute("INSERT INTO Houses VALUES(%s,%s,%s,%s,%s,%s)",(prop_id,rooms,addr,sqft,price,availability))
        elif type_=='Apartments': cur.execute("INSERT INTO Apartments VALUES(%s,%s,%s,%s,%s,%s,%s)",(prop_id,rooms,addr,sqft,price,availability,btype))
        else:cur.execute("INSERT INTO CommBuildings VALUES(%s,%s,%s,%s,%s,%s)",(prop_id,addr,btype,sqft,price,availability))
        cur.execute("INSERT INTO Neighbourhood(PropId,CrimeRate,NearbySchool,Hospital,Park,mart) VALUES(%s,%s,%s,%s,%s,%s)",
                    (prop_id,crime_rate,nearby_school,hospital,park,mart))
        conn.commit();cur.close();conn.close();st.success(f"Added property {prop_id} with neighbourhood info")
        st.session_state.page='view';st.rerun()

# ——— Router ———
def main():
    if 'page' not in st.session_state: st.session_state.page='signup'
    if st.session_state.page=='signup': signup_page()
    elif st.session_state.page=='login': login_page()
    elif st.session_state.page=='view': view_page()
    elif st.session_state.page=='buy': buy_page()
    elif st.session_state.page=='add': add_page()
    elif st.session_state.page == 'edit':edit_page()
    elif st.session_state.page=='profile': profile_page()
    else: st.error(f"Unknown page: {st.session_state.page}")

if __name__=='__main__': main()