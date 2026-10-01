CREATE DATABASE IF NOT EXISTS fieldnote CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS ashford CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS lumen CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS waybill CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS halden CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS stockwell CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS vellum CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'bench'@'%' IDENTIFIED BY 'bench-local-only';
GRANT ALL PRIVILEGES ON fieldnote.* TO 'bench'@'%';
GRANT ALL PRIVILEGES ON ashford.* TO 'bench'@'%';
GRANT ALL PRIVILEGES ON lumen.* TO 'bench'@'%';
GRANT ALL PRIVILEGES ON waybill.* TO 'bench'@'%';
GRANT ALL PRIVILEGES ON halden.* TO 'bench'@'%';
GRANT ALL PRIVILEGES ON stockwell.* TO 'bench'@'%';
GRANT ALL PRIVILEGES ON vellum.* TO 'bench'@'%';
FLUSH PRIVILEGES;

USE fieldnote;

CREATE TABLE IF NOT EXISTS fn_titles (
  id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(180) NOT NULL,
  author_name VARCHAR(120) NOT NULL,
  imprint_year SMALLINT NOT NULL,
  shelf_code VARCHAR(32) NOT NULL
);

INSERT INTO fn_titles (title, author_name, imprint_year, shelf_code) VALUES
('Salt Roads of the Inner Harbor', 'Maeve Alden', 2024, 'FN-204'),
('A Ledger of Winter Birds', 'Ivo March', 2023, 'FN-188'),
('Field Notes from the Clay Works', 'Ruth Pell', 2025, 'FN-231'),
('The Night Ferry Index', 'Jonas Hale', 2022, 'FN-176'),
('Orchards After the Frost', 'Lena Ortiz', 2026, 'FN-240'),
('Maps Drawn for the Canal Board', 'Edith Krohn', 2021, 'FN-164'),
('Glasshouse Weather', 'Samir Adeyemi', 2025, 'FN-227'),
('Portraits of Working Boats', 'Helen Cho', 2024, 'FN-211'),
('A Short History of the Mill Race', 'Patrick Lang', 2020, 'FN-153'),
('Kitchen Gardens of the Ridge', 'Nora Belk', 2026, 'FN-244');

USE ashford;

CREATE TABLE IF NOT EXISTS ar_members (
  id INT PRIMARY KEY AUTO_INCREMENT,
  full_name VARCHAR(120) NOT NULL,
  chapter VARCHAR(80) NOT NULL,
  role_title VARCHAR(80) NOT NULL,
  standing_label VARCHAR(32) NOT NULL,
  biography VARCHAR(400) NOT NULL
);

INSERT INTO ar_members (full_name, chapter, role_title, standing_label, biography) VALUES
('Adele Voss', 'Harbor Chapter', 'Chapter clerk', 'current', 'Keeps the harbor chapter roll and the seasonal work diary for the mudflat surveys.'),
('Bram Keller', 'Harbor Chapter', 'Boat steward', 'current', 'Schedules the skiffs used for eelgrass counts along the inner berths.'),
('Celia Nguyen', 'Estuary Chapter', 'Field lead', 'current', 'Runs the dawn transect from the rail bridge to the old ferry slip.'),
('Dorian Ames', 'Estuary Chapter', 'Archivist', 'leave', 'Catalogues the paper charts the chapter inherited from the pilot association.'),
('Esther Blum', 'Ridge Chapter', 'Warden', 'current', 'Walks the ridge fences after storms and files the repair notes.'),
('Felix Ortega', 'Ridge Chapter', 'Surveyor', 'current', 'Maintains the shared benchmark pins above the clay pits.'),
('Greta Holm', 'Basin Chapter', 'Treasurer', 'current', 'Publishes the quarterly dues sheet for the basin workshop.'),
('Hugo Park', 'Basin Chapter', 'Tool keeper', 'current', 'Signs the pumps and salinity kits in and out of the basin shed.'),
('Irene Dalca', 'Harbor Chapter', 'Editor', 'current', 'Prepares the member circular that goes out with the tide table.'),
('Jules Rahman', 'Estuary Chapter', 'Recorder', 'probation', 'Transcribes the evening counts from the boardwalk stations.'),
('Kira Solano', 'Ridge Chapter', 'Plant lead', 'current', 'Tracks the nursery stock promised to the municipal verges.'),
('Leo Brandt', 'Basin Chapter', 'Safety chair', 'current', 'Reviews the night-landing notes before the work boats go out.'),
('Mina Elwood', 'Harbor Chapter', 'Host', 'current', 'Opens the chart room for the monthly membership hour.'),
('Nils Petrov', 'Estuary Chapter', 'Net mender', 'leave', 'On leave while the chapter loft is rewired.'),
('Opal Singh', 'Ridge Chapter', 'Secretary', 'current', 'Minutes the ridge meetings and posts the decision list.'),
('Pauline Cho', 'Basin Chapter', 'Delegate', 'current', 'Carries the basin report to the seasonal assembly.');

USE lumen;

CREATE TABLE IF NOT EXISTS lc_probes (
  id INT PRIMARY KEY AUTO_INCREMENT,
  service_name VARCHAR(80) NOT NULL,
  region_code VARCHAR(32) NOT NULL,
  latency_ms INT NOT NULL,
  status_label VARCHAR(32) NOT NULL
);

INSERT INTO lc_probes (service_name, region_code, latency_ms, status_label) VALUES
('edge-harbor-01', 'harbor', 18, 'steady'),
('edge-harbor-02', 'harbor', 22, 'steady'),
('edge-harbor-03', 'harbor', 41, 'watch'),
('gate-harbor-04', 'harbor', 16, 'steady'),
('gate-harbor-05', 'harbor', 27, 'steady'),
('cache-harbor-06', 'harbor', 33, 'steady'),
('cache-harbor-07', 'harbor', 58, 'degraded'),
('edge-estuary-01', 'estuary', 24, 'steady'),
('edge-estuary-02', 'estuary', 29, 'steady'),
('edge-estuary-03', 'estuary', 47, 'watch'),
('relay-estuary-04', 'estuary', 19, 'steady'),
('relay-estuary-05', 'estuary', 36, 'steady'),
('span-estuary-06', 'estuary', 21, 'steady'),
('span-estuary-07', 'estuary', 63, 'degraded'),
('edge-ridge-01', 'ridge', 31, 'steady'),
('edge-ridge-02', 'ridge', 28, 'steady'),
('edge-ridge-03', 'ridge', 44, 'watch'),
('tower-ridge-04', 'ridge', 17, 'steady'),
('tower-ridge-05', 'ridge', 26, 'steady'),
('link-ridge-06', 'ridge', 39, 'steady'),
('link-ridge-07', 'ridge', 52, 'watch'),
('edge-basin-01', 'basin', 20, 'steady'),
('edge-basin-02', 'basin', 23, 'steady'),
('edge-basin-03', 'basin', 49, 'watch'),
('pump-basin-04', 'basin', 15, 'steady'),
('pump-basin-05', 'basin', 34, 'steady'),
('meter-basin-06', 'basin', 27, 'steady'),
('meter-basin-07', 'basin', 71, 'degraded');

USE waybill;

CREATE TABLE IF NOT EXISTS wb_shipments (
  id INT PRIMARY KEY AUTO_INCREMENT,
  tracking_code VARCHAR(32) NOT NULL,
  origin_city VARCHAR(80) NOT NULL,
  dest_city VARCHAR(80) NOT NULL,
  status_label VARCHAR(32) NOT NULL,
  booked_on DATE NOT NULL
);

INSERT INTO wb_shipments (tracking_code, origin_city, dest_city, status_label, booked_on) VALUES
('WB-44190', 'Providence', 'New Bedford', 'in transit', '2026-09-12'),
('WB-44191', 'Fall River', 'Newport', 'delivered', '2026-09-14'),
('WB-44202', 'Quincy', 'Salem', 'at dock', '2026-09-18'),
('WB-44218', 'Portland', 'Bath', 'in transit', '2026-09-21'),
('WB-44240', 'Hudson', 'Troy', 'held', '2026-09-22'),
('WB-44255', 'Kingston', 'Poughkeepsie', 'delivered', '2026-09-25'),
('WB-44271', 'Camden', 'Trenton', 'in transit', '2026-09-28'),
('WB-44288', 'Annapolis', 'Baltimore', 'at dock', '2026-09-30');

USE halden;

CREATE TABLE IF NOT EXISTS hs_programs (
  code VARCHAR(32) PRIMARY KEY,
  title VARCHAR(120) NOT NULL
);

INSERT INTO hs_programs (code, title) VALUES
('history', 'Early modern history'),
('letters', 'Correspondence and letters'),
('botany', 'Field botany'),
('cartography', 'Chart and map study');

USE stockwell;

CREATE TABLE IF NOT EXISTS sw_holdings (
  id INT PRIMARY KEY AUTO_INCREMENT,
  asset_tag VARCHAR(32) NOT NULL,
  asset_name VARCHAR(160) NOT NULL,
  site_name VARCHAR(80) NOT NULL,
  category_name VARCHAR(64) NOT NULL,
  status_label VARCHAR(32) NOT NULL,
  acquired_on DATE NOT NULL,
  book_value DECIMAL(12,2) NOT NULL
);

INSERT INTO sw_holdings (asset_tag, asset_name, site_name, category_name, status_label, acquired_on, book_value) VALUES
('SW-1008', 'Oak reading table', 'Civic hall', 'furniture', 'in_service', '2018-04-12', 2400.00),
('SW-1014', 'Plan chest, eight drawer', 'Survey office', 'furniture', 'in_service', '2016-11-02', 3100.00),
('SW-1044', 'Microfilm reader', 'Archive annex', 'equipment', 'in_repair', '2014-06-19', 860.00),
('SW-1102', 'Harbor light fixture set', 'Pier store', 'fixtures', 'in_service', '2021-03-08', 5400.00),
('SW-1120', 'Salt shed doors', 'Works yard', 'structure', 'in_service', '2019-09-30', 7200.00),
('SW-1188', 'Drafting stools', 'Survey office', 'furniture', 'surplus', '2013-01-22', 640.00),
('SW-1206', 'Pump house meter bank', 'Basin works', 'equipment', 'in_service', '2022-07-14', 12850.00),
('SW-1219', 'Ridge gate motor', 'North fence', 'equipment', 'in_repair', '2020-05-11', 4300.00),
('SW-1301', 'Map cabinet', 'Civic hall', 'furniture', 'in_service', '2017-08-09', 1900.00),
('SW-1333', 'Gallery rail', 'Civic hall', 'fixtures', 'in_service', '2015-12-01', 2750.00),
('SW-1408', 'Flatbed scanner', 'Archive annex', 'equipment', 'archived', '2011-02-17', 220.00),
('SW-1440', 'Workshop vise row', 'Works yard', 'equipment', 'in_service', '2018-10-05', 1680.00),
('SW-1512', 'Clerk counter', 'Records desk', 'furniture', 'in_service', '2023-01-20', 4100.00),
('SW-1566', 'Window blinds, east wing', 'Civic hall', 'fixtures', 'surplus', '2012-04-28', 480.00),
('SW-1604', 'Diesel heater', 'Pier store', 'equipment', 'in_service', '2019-11-16', 2350.00),
('SW-1677', 'Chain hoist', 'Works yard', 'equipment', 'in_repair', '2016-03-03', 990.00),
('SW-1720', 'Binding press', 'Archive annex', 'equipment', 'in_service', '2024-02-12', 3560.00),
('SW-1784', 'Notice board run', 'Records desk', 'fixtures', 'in_service', '2020-09-01', 740.00),
('SW-1811', 'Clay sample cabinet', 'Survey office', 'furniture', 'in_service', '2025-06-18', 1280.00),
('SW-1902', 'Spare pontoon', 'Pier store', 'structure', 'archived', '2009-07-23', 1500.00);

USE vellum;

CREATE TABLE IF NOT EXISTS vm_folios (
  id INT PRIMARY KEY AUTO_INCREMENT,
  shelf_code VARCHAR(32) NOT NULL,
  siglum VARCHAR(32) NOT NULL,
  work_title VARCHAR(180) NOT NULL,
  scribe_name VARCHAR(120) NOT NULL,
  leaf_no INT NOT NULL,
  century_label VARCHAR(32) NOT NULL,
  incipit VARCHAR(240) NOT NULL
);

INSERT INTO vm_folios (shelf_code, siglum, work_title, scribe_name, leaf_no, century_label, incipit) VALUES
('west-cloister', 'MS-14', 'Harbor customary', 'Anonymous, west hand', 1, '15th century', 'Here begins the order of the night watch along the inner quay.'),
('west-cloister', 'MS-14', 'Harbor customary', 'Anonymous, west hand', 2, '15th century', 'The second leaf names the bells and who must answer them.'),
('west-cloister', 'MS-18', 'Garden receipts', 'Sister Alma', 4, '16th century', 'Take the seed after the last frost and set it in the south bed.'),
('west-cloister', 'MS-18', 'Garden receipts', 'Sister Alma', 5, '16th century', 'Of rosemary kept through a hard winter in a clay pot.'),
('east-stack', 'MS-22', 'Pilot letters', 'John Hare', 3, '17th century', 'To the warden of the estuary, concerning the shifted bar.'),
('east-stack', 'MS-22', 'Pilot letters', 'John Hare', 6, '17th century', 'A further note on the lantern kept at the bend.'),
('east-stack', 'MS-27', 'Mill accounts', 'Clerk of the race', 8, '16th century', 'Received for the grinding of the manor wheat, Michaelmas.'),
('east-stack', 'MS-31', 'Choir ordinal', 'Canon Ellis', 2, '15th century', 'The respond for the feast when the river procession is kept.'),
('scriptorium', 'MS-40', 'Dye book', 'Marta Quinn', 1, '18th century', 'Madder, weld, and the iron liquor used on sailcloth.'),
('scriptorium', 'MS-40', 'Dye book', 'Marta Quinn', 7, '18th century', 'A margin note on indigo that failed in a wet June.'),
('annex', 'MS-51', 'Boundary perambulation', 'Town clerk', 9, '17th century', 'From the oak at the ridge road to the stone in the basin meadow.'),
('annex', 'MS-55', 'Shipwright notes', 'Elias Ward', 3, '18th century', 'Scantlings for a work boat of twenty-two feet.');
