--
-- SQL script to create the new offline dropBox database log
--

drop table fileLog;
drop table runLog;
commit;

CREATE TABLE runLog (
    creationTimestamp TIMESTAMP NOT NULL CONSTRAINT ckRunLogCrets CHECK (creationTimestamp > to_date('2012-01-01', 'YYYY-MM-DD')),
    statusCode NUMBER NOT NULL,
    firstConditionSafeRun NUMBER CONSTRAINT ckFirstConditionSafeRun CHECK (firstConditionSafeRun > 0),
    hltRun NUMBER CONSTRAINT ckHltRun CHECK (hltRun > 0),
    downloadLog CLOB,
    globalLog CLOB,
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
    username VARCHAR2(100 BYTE) NOT NULL,
    log CLOB,
    runLogCreationTimestamp TIMESTAMP CONSTRAINT ckFileLogRunLogCrets CHECK (runLogCreationTimestamp > to_date('2012-01-01', 'YYYY-MM-DD')),
    creationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL CONSTRAINT ckFileLogCrets CHECK (creationTimestamp > to_date('2012-01-01', 'YYYY-MM-DD')),
    modificationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (fileHash),
    CONSTRAINT ckFileLogModGtCre CHECK (modificationTimestamp >= creationTimestamp),
    CONSTRAINT fkFileLogRunLogCre FOREIGN KEY (runLogCreationTimestamp) REFERENCES runLog (creationTimestamp)
)
;

create or replace trigger tumFileLog
before update on fileLog
for each row
begin
        :new.modificationTimestamp := CURRENT_TIMESTAMP;
end;
/

commit;

