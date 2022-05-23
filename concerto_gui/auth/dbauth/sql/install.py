from __future__ import absolute_import, division, print_function, unicode_literals

from concerto_gui.database import SQLScript

from concerto_gui import version


class SQLUpdate(SQLScript):
    type = "install"
    branch = version.__branch__
    version = "0"

    def run(self):
        self.query("""
DROP TABLE IF EXISTS Concerto_User_Group;

CREATE TABLE Concerto_User_Group (
        groupid VARCHAR(32) NOT NULL,
        userid VARCHAR(32) NOT NULL,
        PRIMARY KEY (groupid, userid),
        FOREIGN KEY (groupid) REFERENCES Concerto_Group(groupid) ON DELETE CASCADE,
        FOREIGN KEY (userid) REFERENCES Concerto_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;
""")
