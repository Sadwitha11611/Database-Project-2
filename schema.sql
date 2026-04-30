DROP DATABASE IF EXISTS airport_db;
CREATE DATABASE airport_db;
USE airport_db;

CREATE TABLE AIRPORT (
    Airport_code CHAR(3) PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    City VARCHAR(50) NOT NULL,
    State VARCHAR(50)
);

CREATE TABLE AIRPLANE_TYPE (
    Type_name VARCHAR(50) PRIMARY KEY,
    Company VARCHAR(50) NOT NULL,
    Max_seats INT NOT NULL
);

CREATE TABLE AIRPLANE (
    Airplane_id VARCHAR(20) PRIMARY KEY,
    Total_no_of_seats INT NOT NULL,
    Type_name VARCHAR(50) NOT NULL,
    FOREIGN KEY (Type_name) REFERENCES AIRPLANE_TYPE(Type_name)
);

CREATE TABLE CAN_LAND (
    Airport_code CHAR(3) NOT NULL,
    Type_name VARCHAR(50) NOT NULL,
    PRIMARY KEY (Airport_code, Type_name),
    FOREIGN KEY (Airport_code) REFERENCES AIRPORT(Airport_code),
    FOREIGN KEY (Type_name) REFERENCES AIRPLANE_TYPE(Type_name)
);

CREATE TABLE FLIGHT (
    Number VARCHAR(10) PRIMARY KEY,
    Airline VARCHAR(50) NOT NULL,
    Weekdays VARCHAR(20) NOT NULL
);

CREATE TABLE FLIGHT_LEG (
    Number VARCHAR(10) NOT NULL,
    Leg_no INT NOT NULL,
    Dep_airport_code CHAR(3) NOT NULL,
    Arr_airport_code CHAR(3) NOT NULL,
    Scheduled_dep_time TIME NOT NULL,
    Scheduled_arr_time TIME NOT NULL,
    PRIMARY KEY (Number, Leg_no),
    FOREIGN KEY (Number) REFERENCES FLIGHT(Number),
    FOREIGN KEY (Dep_airport_code) REFERENCES AIRPORT(Airport_code),
    FOREIGN KEY (Arr_airport_code) REFERENCES AIRPORT(Airport_code)
);

CREATE TABLE FARE (
    Number VARCHAR(10) NOT NULL,
    Code VARCHAR(20) NOT NULL,
    Amount DECIMAL(10, 2) NOT NULL,
    Restriction VARCHAR(100),
    PRIMARY KEY (Number, Code),
    FOREIGN KEY (Number) REFERENCES FLIGHT(Number)
);

CREATE TABLE LEG_INSTANCE (
    Date DATE NOT NULL,
    Number VARCHAR(10) NOT NULL,
    Leg_no INT NOT NULL,
    No_of_avail_seats INT NOT NULL,
    Airplane_id VARCHAR(20) NOT NULL,
    Dep_time TIME,
    Arr_time TIME,
    PRIMARY KEY (Date, Number, Leg_no),
    FOREIGN KEY (Number, Leg_no) REFERENCES FLIGHT_LEG(Number, Leg_no),
    FOREIGN KEY (Airplane_id) REFERENCES AIRPLANE(Airplane_id)
);

CREATE TABLE SEAT (
    Airplane_id VARCHAR(20) NOT NULL,
    Seat_no VARCHAR(5) NOT NULL,
    Class VARCHAR(20) NOT NULL,
    PRIMARY KEY (Airplane_id, Seat_no),
    FOREIGN KEY (Airplane_id) REFERENCES AIRPLANE(Airplane_id)
);

CREATE TABLE RESERVATION (
    Date DATE NOT NULL,
    Number VARCHAR(10) NOT NULL,
    Leg_no INT NOT NULL,
    Airplane_id VARCHAR(20) NOT NULL,
    Seat_no VARCHAR(5) NOT NULL,
    Customer_name VARCHAR(100) NOT NULL,
    Cphone VARCHAR(20) NOT NULL,
    PRIMARY KEY (Date, Number, Leg_no, Seat_no),
    FOREIGN KEY (Date, Number, Leg_no) REFERENCES LEG_INSTANCE(Date, Number, Leg_no),
    FOREIGN KEY (Airplane_id, Seat_no) REFERENCES SEAT(Airplane_id, Seat_no)
);
