from __future__ import absolute_import, division, print_function, unicode_literals

from concerto_gui import version
from concerto_gui.database import SQLScript


class SQLUpdate(SQLScript):
    type = "install"
    branch = version.__branch__
    version = "0"

    def run(self):
        self.query("""
DROP TABLE IF EXISTS Concerto_Module_Changed;
CREATE TABLE Concerto_Module_Changed (
    time DATETIME NOT NULL
) ENGINE=InnoDB;

INSERT INTO Concerto_Module_Changed (time) VALUES(current_timestamp);


DROP TABLE IF EXISTS Concerto_Module_Registry;
CREATE TABLE Concerto_Module_Registry (
    module VARCHAR(255) NOT NULL PRIMARY KEY,
    enabled TINYINT DEFAULT 1,
    branch VARCHAR(16) NULL,
    version VARCHAR(16) NULL
) ENGINE=InnoDB;


DROP TABLE IF EXISTS Concerto_History_Query;
DROP TABLE IF EXISTS Concerto_Crontab;
DROP TABLE IF EXISTS Concerto_Session;
DROP TABLE IF EXISTS Concerto_User_Configuration;
DROP TABLE IF EXISTS Concerto_User_Permission;
DROP TABLE IF EXISTS Concerto_User;


CREATE TABLE Concerto_User (
    name VARCHAR(255) NOT NULL,
    userid VARCHAR(32) NOT NULL PRIMARY KEY
) ENGINE=InnoDB;

CREATE INDEX concerto_gui_user_index_name ON Concerto_User (name);


CREATE TABLE Concerto_User_Permission (
    userid VARCHAR(32) NOT NULL,
    permission VARCHAR(32) NOT NULL,
    PRIMARY KEY (userid, permission),
    FOREIGN KEY (userid) REFERENCES Concerto_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;


DROP TABLE IF EXISTS Concerto_Group_Permission;
DROP TABLE IF EXISTS Concerto_Group;


CREATE TABLE Concerto_Group (
    name VARCHAR(255) NOT NULL,
    groupid VARCHAR(32) NOT NULL PRIMARY KEY
) ENGINE=InnoDB;

CREATE INDEX concerto_gui_group_index_name ON Concerto_Group (name);


CREATE TABLE Concerto_Group_Permission (
    groupid VARCHAR(32) NOT NULL,
    permission VARCHAR(32) NOT NULL,
    PRIMARY KEY (groupid, permission),
    FOREIGN KEY (groupid) REFERENCES Concerto_Group(groupid) ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE Concerto_Session (
    sessionid VARCHAR(48) NOT NULL PRIMARY KEY,
    userid VARCHAR(32) NOT NULL,
    login VARCHAR(255) NOT NULL,
    time DATETIME NOT NULL,
    FOREIGN KEY (userid) REFERENCES Concerto_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE Concerto_User_Configuration (
    userid VARCHAR(255) NOT NULL,
    config TEXT NULL,
    PRIMARY KEY (userid),
    FOREIGN KEY (userid) REFERENCES Concerto_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE Concerto_Crontab (
    id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    userid VARCHAR(32) NULL,
    schedule VARCHAR(32) NULL,
    ext_type VARCHAR(255) NULL,
    ext_id INTEGER NULL,
    base DATETIME NOT NULL,
    enabled TINYINT DEFAULT 1,
    runcnt  INTEGER DEFAULT 0,
    error TEXT NULL,
    FOREIGN KEY (userid) REFERENCES Concerto_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE Concerto_History_Query (
    userid VARCHAR(32) NOT NULL,
    formid VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    query_hash VARCHAR(32) NOT NULL,
    timestamp DATETIME NOT NULL,
    PRIMARY KEY (userid, formid, query_hash),
    FOREIGN KEY (userid) REFERENCES Concerto_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;
""")
