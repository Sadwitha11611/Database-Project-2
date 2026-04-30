USE airport_db;

-- Optional demo reservations for the Milestone 2 passenger/booking queries.
-- Run this only after schema.sql and the professor CSV data have been loaded.

INSERT IGNORE INTO RESERVATION
(Date, Number, Leg_no, Airplane_id, Seat_no, Customer_name, Cphone)
VALUES
('2025-10-04', '1000', 1, 'PLNEDAB43C9', '1A', 'John Smith', '2145550101'),
('2025-10-04', '1000', 1, 'PLNEDAB43C9', '1B', 'Priya Narayan', '2145550102'),
('2025-10-04', '1000', 2, 'PLNEDAB43C9', '1A', 'John Smith', '2145550101'),
('2025-10-04', '1000', 2, 'PLNEDAB43C9', '1C', 'Maria Garcia', '2145550103');
