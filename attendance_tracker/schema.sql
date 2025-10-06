-- schema.sql
CREATE DATABASE IF NOT EXISTS attendance_tracker;
USE attendance_tracker;

-- Admins (system admin accounts)
CREATE TABLE admins (
  admin_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- students
CREATE TABLE students (
  enrol_no VARCHAR(20) PRIMARY KEY,
  class_roll INT NOT NULL,
  name VARCHAR(150) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  email VARCHAR(150),
  parent_email VARCHAR(150),
  year INT NOT NULL,
  section VARCHAR(10) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- professors (teachers)
CREATE TABLE professors (
  prof_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) UNIQUE NOT NULL,
  name VARCHAR(150) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  email VARCHAR(150),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- subjects
CREATE TABLE subjects (
  sub_id INT AUTO_INCREMENT PRIMARY KEY,
  sub_name VARCHAR(200) NOT NULL,
  year INT NOT NULL
);

-- many-to-many: students <-> subjects (enrollment)
CREATE TABLE student_subjects (
  enrol_no VARCHAR(20),
  sub_id INT,
  PRIMARY KEY (enrol_no, sub_id),
  FOREIGN KEY (enrol_no) REFERENCES students(enrol_no) ON DELETE CASCADE,
  FOREIGN KEY (sub_id) REFERENCES subjects(sub_id) ON DELETE CASCADE
);

-- many-to-many: professors <-> subjects (teaching assignments)
CREATE TABLE professor_subjects (
  prof_id INT,
  sub_id INT,
  PRIMARY KEY (prof_id, sub_id),
  FOREIGN KEY (prof_id) REFERENCES professors(prof_id) ON DELETE CASCADE,
  FOREIGN KEY (sub_id) REFERENCES subjects(sub_id) ON DELETE CASCADE
);

-- routine / timetable (a row = one scheduled class slot)
CREATE TABLE routine (
  routine_id INT AUTO_INCREMENT PRIMARY KEY,
  day ENUM('Mon','Tue','Wed','Thu','Fri','Sat','Sun') NOT NULL,
  timing VARCHAR(50) NOT NULL, -- e.g. "09:00-09:50"
  year INT NOT NULL,
  section VARCHAR(10) NOT NULL,
  sub_id INT NOT NULL,
  prof_id INT NOT NULL,
  FOREIGN KEY (sub_id) REFERENCES subjects(sub_id),
  FOREIGN KEY (prof_id) REFERENCES professors(prof_id),
  UNIQUE KEY uniq_routine_slot (day, timing, year, section, sub_id)
);

-- attendance: one record per student per date per period (linked to routine_id)
CREATE TABLE attendance (
  attendance_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  enrol_no VARCHAR(20) NOT NULL,
  class_date DATE NOT NULL,
  routine_id INT NULL,
  period VARCHAR(50) NULL,
  sub_id INT NULL,
  prof_id INT NULL,
  status ENUM('present','absent','leave','late') NOT NULL DEFAULT 'present',
  marked_by INT NULL, -- prof_id who marked it (nullable for imports)
  remarks VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (enrol_no) REFERENCES students(enrol_no) ON DELETE CASCADE,
  FOREIGN KEY (routine_id) REFERENCES routine(routine_id) ON DELETE SET NULL,
  FOREIGN KEY (sub_id) REFERENCES subjects(sub_id),
  FOREIGN KEY (prof_id) REFERENCES professors(prof_id),
  INDEX idx_student_date (enrol_no, class_date),
  INDEX idx_date (class_date)
);

-- optional stats cache table
CREATE TABLE attendance_stats (
  enrol_no VARCHAR(20),
  sub_id INT,
  total_classes INT DEFAULT 0,
  attended INT DEFAULT 0,
  PRIMARY KEY (enrol_no, sub_id),
  FOREIGN KEY (enrol_no) REFERENCES students(enrol_no),
  FOREIGN KEY (sub_id) REFERENCES subjects(sub_id)
);
