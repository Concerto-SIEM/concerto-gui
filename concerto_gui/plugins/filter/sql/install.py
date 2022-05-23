from __future__ import absolute_import, division, print_function, unicode_literals

from concerto_gui import version
from concerto_gui.database import SQLScript


class SQLUpdate(SQLScript):
    type = "install"
    branch = version.__branch__
    version = "0"

    def run(self):
        self.query("""
DROP TABLE IF EXISTS Concerto_Filter;

CREATE TABLE Concerto_Filter (
        id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
        userid VARCHAR(32) NOT NULL,
        name VARCHAR(64) NOT NULL,
        category VARCHAR(64) NULL,
        description TEXT NULL,
        value TEXT NOT NULL,
        FOREIGN KEY (userid) REFERENCES Concerto_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE UNIQUE INDEX concerto_gui_filter_index_login_name ON Concerto_Filter (userid, name);
""")
