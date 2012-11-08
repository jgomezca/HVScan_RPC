--
-- SQL script to create the new frontend dropBox database
--

drop table fileLog;
drop table runLog;
drop table files;

CREATE TABLE files (
    fileHash VARCHAR2(40 BYTE) NOT NULL,
    state VARCHAR2(12 BYTE) NOT NULL CONSTRAINT ckFilesState CHECK (state in ('Uploaded', 'Pending', 'Acknowledged', 'Bad')),
    backend VARCHAR2(20 BYTE) NOT NULL,
    username VARCHAR2(100 BYTE) NOT NULL,
    fileContent BLOB,
    creationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL CONSTRAINT ckFilesCrets CHECK (creationTimestamp > to_date('2012-01-01', 'YYYY-MM-DD')),
    modificationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (fileHash),
    CONSTRAINT ckFilesModGtCre CHECK (modificationTimestamp >= creationTimestamp)
)
;

create index idxFilesState on files (state, backend);

create or replace trigger tumFiles
before update on files
for each row
begin
        :new.modificationTimestamp := CURRENT_TIMESTAMP;
end;
/

CREATE TABLE runLog (
    creationTimestamp TIMESTAMP NOT NULL CONSTRAINT ckRunLogCrets CHECK (creationTimestamp > to_date('2012-01-01', 'YYYY-MM-DD')),
    statusCode NUMBER NOT NULL,
    firstConditionSafeRun NUMBER CONSTRAINT ckFirstConditionSafeRun CHECK (firstConditionSafeRun >= 0),
    hltRun NUMBER CONSTRAINT ckHltRun CHECK (hltRun >= 0),
    downloadLog BLOB,
    globalLog BLOB,
    modificationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (creationTimestamp),
    CONSTRAINT ckRunLogModGtCre CHECK (modificationTimestamp >= creationTimestamp)
)
;

create or replace trigger tumRunLog
before update on runLog
for each row
begin
        :new.modificationTimestamp := CURRENT_TIMESTAMP;
end;
/

CREATE TABLE fileLog (
    fileHash VARCHAR2(40 BYTE) NOT NULL,
    statusCode NUMBER NOT NULL,
    metadata VARCHAR2(4000 BYTE),
    userText VARCHAR2(4000 BYTE),
    log BLOB,
    runLogCreationTimestamp TIMESTAMP CONSTRAINT ckFileLogRunLogCrets CHECK (runLogCreationTimestamp > to_date('2012-01-01', 'YYYY-MM-DD')),
    creationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL CONSTRAINT ckFileLogCrets CHECK (creationTimestamp > to_date('2012-01-01', 'YYYY-MM-DD')),
    modificationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (fileHash),
    CONSTRAINT ckFileLogModGtCre CHECK (modificationTimestamp >= creationTimestamp),
    CONSTRAINT fkFileLogFilesFileHash FOREIGN KEY (fileHash) REFERENCES files (fileHash),
    CONSTRAINT fkFileLogRunLogCre FOREIGN KEY (runLogCreationTimestamp) REFERENCES runLog (creationTimestamp)
)
;

create index idxFileLogRunLogCrets on fileLog (runLogCreationTimestamp);

create or replace trigger tumFileLog
before update on fileLog
for each row
begin
        :new.modificationTimestamp := CURRENT_TIMESTAMP;
end;
/

commit;

