--
-- SQL script to create the new frontend dropBox database
--

drop table emails;
drop sequence seqEmailsId;
drop table fileAcks;
drop table fileLog;
drop table runLog;
drop table files;

CREATE TABLE files (
    fileHash VARCHAR2(40 BYTE) NOT NULL,
    state VARCHAR2(12 BYTE) NOT NULL CONSTRAINT ckFilesState CHECK (state in ('Uploaded', 'Pending', 'Acknowledged', 'Bad')),
    backend VARCHAR2(20 BYTE) NOT NULL,
    username VARCHAR2(100 BYTE) NOT NULL,
    fileName VARCHAR2(255 BYTE) NOT NULL,
    fileContent BLOB,
    creationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL CONSTRAINT ckFilesCrets CHECK (creationTimestamp > to_date('2012-01-01', 'YYYY-MM-DD')),
    modificationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (fileHash),
    CONSTRAINT ckFilesModGtCre CHECK (modificationTimestamp >= creationTimestamp)
)
;

create index idxFilesState on files (state, backend);

-- for Gianluca and others since they will query the original filename often
create index idxFilesFileName on files (fileName);

create or replace trigger tumFiles
before update on files
for each row
begin
        :new.modificationTimestamp := CURRENT_TIMESTAMP;
end;
/

CREATE TABLE runLog (
    creationTimestamp TIMESTAMP NOT NULL CONSTRAINT ckRunLogCrets CHECK (creationTimestamp > to_date('2012-01-01', 'YYYY-MM-DD')),
    backend VARCHAR2(20 BYTE) NOT NULL,
    statusCode NUMBER NOT NULL,
    firstConditionSafeRun NUMBER CONSTRAINT ckFirstConditionSafeRun CHECK (firstConditionSafeRun >= 0),
    hltRun NUMBER CONSTRAINT ckHltRun CHECK (hltRun >= 0),
    downloadLog BLOB,
    globalLog BLOB,
    modificationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (backend, creationTimestamp),
    CONSTRAINT ckRunLogModGtCre CHECK (modificationTimestamp >= creationTimestamp)
)
;

create index idxRunLogCrets on runLog (creationTimestamp);

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
    runLogBackend VARCHAR2(20 BYTE),
    creationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL CONSTRAINT ckFileLogCrets CHECK (creationTimestamp > to_date('2012-01-01', 'YYYY-MM-DD')),
    modificationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (fileHash),
    CONSTRAINT ckFileLogModGtCre CHECK (modificationTimestamp >= creationTimestamp),
    CONSTRAINT fkFileLogFilesFileHash FOREIGN KEY (fileHash) REFERENCES files (fileHash),
    CONSTRAINT fkFileLogRunLogBackendCrets FOREIGN KEY (runLogBackend, runLogCreationTimestamp) REFERENCES runLog (backend, creationTimestamp)
)
;

create index idxFileLogRunLogBackendCrets on fileLog (runLogBackend, runLogCreationTimestamp);
create index idxFileLogRunLogCrets on fileLog (runLogCreationTimestamp);

create or replace trigger tumFileLog
before update on fileLog
for each row
begin
        :new.modificationTimestamp := CURRENT_TIMESTAMP;
end;
/

CREATE TABLE fileAcks (
    fileHash VARCHAR2(40 BYTE) NOT NULL,
    username VARCHAR2(100 BYTE) NOT NULL,
    rationale VARCHAR2(4000 BYTE),
    creationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL CONSTRAINT ckFileAcksCrets CHECK (creationTimestamp > to_date('2012-01-01', 'YYYY-MM-DD')),
    modificationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (fileHash),
    CONSTRAINT ckFileAcksModGtCre CHECK (modificationTimestamp >= creationTimestamp),
    CONSTRAINT fkFileAcksFileLogFileHash FOREIGN KEY (fileHash) REFERENCES fileLog (fileHash)
)
;

create or replace trigger tumFileAcks
before update on fileAcks
for each row
begin
        :new.modificationTimestamp := CURRENT_TIMESTAMP;
end;
/

CREATE TABLE emails (
    id NUMBER NOT NULL,
    subject VARCHAR2(1000 BYTE) NOT NULL,
    body BLOB NOT NULL,
    fromAddress VARCHAR2(200 BYTE) NOT NULL,
    toAddresses VARCHAR2(4000 BYTE) NOT NULL,
    ccAddresses VARCHAR2(4000 BYTE) NULL,
    creationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL CONSTRAINT ckEmailsCrets CHECK (creationTimestamp > to_date('2012-01-01', 'YYYY-MM-DD')),
    modificationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
)
;

create sequence seqEmailsId
start with 1
increment by 1
nocache
nocycle;

create or replace trigger trgEmailsId
before insert on emails
for each row
begin
  select seqEmailsId.nextval into :new.id from dual;
end;
/

create or replace trigger tumEmails
before update on emails
for each row
begin
        :new.modificationTimestamp := CURRENT_TIMESTAMP;
end;
/

commit;

