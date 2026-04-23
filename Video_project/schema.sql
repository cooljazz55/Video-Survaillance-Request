PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id TEXT NOT NULL UNIQUE,
  first_name TEXT NOT NULL,
  last_name  TEXT NOT NULL,
  email      TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('requestor','director','tech','admin')),
  department TEXT,
  division TEXT,
  job_title TEXT,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS footage_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  requestor_id INTEGER NOT NULL,
  division TEXT,
  job_title TEXT,
  building TEXT,
  camera_location TEXT NOT NULL,
  start_time TEXT NOT NULL,
  end_time   TEXT NOT NULL,
  reason TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'Pending'
    CHECK (status IN ('Pending','Approved','Denied','Completed')),
  director_id INTEGER,
  director_comment TEXT,
  decided_at TEXT,
  tech_id INTEGER,
  completed_at TEXT,
  footage_path TEXT,
  submitted_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (requestor_id) REFERENCES users(id),
  FOREIGN KEY (director_id)  REFERENCES users(id),
  FOREIGN KEY (tech_id)      REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  action TEXT NOT NULL,
  request_id INTEGER,
  ip_address TEXT,
  user_agent TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (request_id) REFERENCES footage_requests(id)
);

CREATE TABLE IF NOT EXISTS footage_deliveries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL,
  provided_at TEXT NOT NULL DEFAULT (datetime('now')),
  technician_name TEXT NOT NULL,
  technician_employee_id TEXT NOT NULL,
  folder_password TEXT NOT NULL,
  footage_location TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (request_id) REFERENCES footage_requests(id)
);

CREATE INDEX IF NOT EXISTS idx_requests_requestor ON footage_requests(requestor_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON footage_requests(status);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_request ON audit_logs(request_id);