CREATE table Users
	(Name_ VARCHAR(30),
	 address VARCHAR(50),
	 Email VARCHAR(50),
	 UserType VARCHAR(7),
	 PRIMARY KEY(Email));

CREATE table Agent
	(AgentID VARCHAR(10),
	 JobTitle VARCHAR(25),
	 Email VARCHAR(50),
	 AgencyName VARCHAR(25),
	 PRIMARY KEY(AgentID),
	 FOREIGN KEY (Email) references Users);

CREATE table Renter
	(RenterID VARCHAR(10),
	 Movein_date DATE,
	 Email VARCHAR(50),
	 PrefLocation VARCHAR(25),
	 Budget numeric(12,2),
	 PRIMARY KEY(RenterID),
	 FOREIGN KEY (Email) references Users);

CREATE table Property
	(

	PropId VARCHAR(10),
	 PropType VARCHAR(15),
	 Description VARCHAR(50),
	 City VARCHAR(12),
	 State_ VARCHAR(12),
	 AgentID Varchar(10),
	 PRIMARY KEY(PropId),
	 FOREIGN KEY (AgentID) REFERENCES Agent);

CREATE table VacHome
	(VacHomeId VARCHAR(10),
	 NoOfRooms numeric(2,0),
	 address VARCHAR(50),
	 SqFootage numeric(7,2),
	 Price numeric(12,2),
	 Availablity Boolean,
	 PRIMARY KEY(VacHomeId),
	 FOREIGN KEY (VacHomeId) references Property);

CREATE table Houses
	(HouseId VARCHAR(10),
	 NoOfRooms numeric(2,0),
	 address VARCHAR(50),
	 SqFootage numeric(7,2),
	 Price numeric(12,2),
	 Availablity Boolean,
	 PRIMARY KEY(HouseId),
	 FOREIGN KEY (HouseId) references Property);

CREATE table Apartments
	(AptId VARCHAR(10),
	 NoOfRooms numeric(2,0),
	 address VARCHAR(50),
	 SqFootage numeric(7,2),
	 Price numeric(12,2),
	 Availablity Boolean,
	 BuildingType VARCHAR(15),
	 PRIMARY KEY(AptId),
	 FOREIGN KEY (AptId) references Property);

CREATE table CommBuildings
	(BuildId VARCHAR(10),
	 address VARCHAR(50),
	 BusinessType VARCHAR(25),
	 SqFootage numeric(7,2),
	 Price numeric(12,2),
	 Availablity Boolean,
	 PRIMARY KEY(BuildId),
	 FOREIGN KEY (BuildId) references Property);

CREATE table Neighbourhood
	(PropId VARCHAR(10),
	 CrimeRate numeric(4,2),
	 NearbySchool VARCHAR(12),
	 Hospital VARCHAR(12),
	 Park VARCHAR(12),
	 mart VARCHAR(12),
	 PRIMARY KEY(PropId, CrimeRate, NearbySchool,Hospital,park,mart),
	 FOREIGN KEY(PropId) references Property);

CREATE table Booking
	(RenterID VARCHAR(10),
	BookID VARCHAR(10),
	PropId VARCHAR(10),
	 StartDate DATE,
	 EndDate DATE,
	 Mode_of_pay VARCHAR(10),
	 TotalCost numeric(12,2),
	 PRIMARY KEY(BookID),
	FOREIGN KEY(RenterID) references Renter,
	FOREIGN KEY (PropId) REFERENCES Property(PropId););

CREATE TABLE Rewards
	(
		R_id VARCHAR(10),
		Reward_Points NUMERIC(6,0),
		PRIMARY KEY (R_id),
		FOREIGN KEY (R_id) references Renter

	);

CREATE table Address
	(RenterID VARCHAR(10),
	 Street VARCHAR(10),
	 city VARCHAR(10),
	 State_ VARCHAR(10),
	 Zip NUMERIC(5),
	 PRIMARY KEY(RenterID, Street,city,State_,Zip),
	 FOREIGN KEY(RenterID) references Renter);

CREATE table CreditCard
	(
	RenterID VARCHAR(10),
	Card_name VARCHAR(25),
	 Card_no NUMERIC(16,0),
	 exp_date DATE,
	 cvv NUMERIC(3),
	 PRIMARY KEY(Card_no,Card_name, exp_date,cvv),
	FOREIGN KEY(RenterID) references Renter);