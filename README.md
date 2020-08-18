# section_parser

Examples:


python3 section_parser.py --xml --file aaaModLR.xml --sort created >> parsed_aaa.txt
python3 section_parser.py --xml --file aaaModLR.xml --sort created --retro --space  >> retro_aaa.txt
python3 section_parser.py --json --file eventRecord.json --sort created --retro --full >> retro_full_events.txt


Traditional section parser worsk with JSON and XML, and you can sort on any field in the object.

The retro option tries to mimic NXOS logs and will condense most info down to one line. The DN part of the log
will be truncated to 40 characters to conserver space in the line.  This is on by default. Retro options
only work with aaaModLR, faultRecord, and eventRecord.  It also has the following options:

--month  >> convert decimal months to alphabetical months
--full   >> prints the full DN (no longer truncated at 40 characters)
--space  >> adds a space when there is a 5 second gap in outputs. This is useful for aaaModLR logs,
            as a single command from the GUI can generate many lines in the aaa logs.  This option
            makes the single configuration changes more noticeable.


icurl log collection examples:

    bash
    icurl 'http://localhost:7777/api/class/aaaModLR.xml?order-by=aaaModLR.created|desc&page-size=100000' > aaaModLR.xml
    icurl 'http://localhost:7777/api/class/faultRecord.xml?order-by=faultRecord.created|desc&page-size=100000' > faultRecord.xml
    icurl 'http://localhost:7777/api/class/eventRecord.xml?order-by=eventRecord.created|desc&page-size=100000' > eventRecord.xml 

    
To grab multiple pages:

    icurl 'http://localhost:7777/api/class/eventRecord.xml?order-by=eventRecord.created|desc&page-size=100000&page=0' > /tmp/tac-outputs/eventRecord.xml
    icurl 'http://localhost:7777/api/class/eventRecord.xml?order-by=eventRecord.created|desc&page-size=100000&page=1' > /tmp/tac-outputs/eventRecord2.xml
    icurl 'http://localhost:7777/api/class/eventRecord.xml?order-by=eventRecord.created|desc&page-size=100000&page=2' > /tmp/tac-outputs/eventRecord3.xml
    icurl 'http://localhost:7777/api/class/eventRecord.xml?order-by=eventRecord.created|desc&page-size=100000&page=3' > /tmp/tac-outputs/eventRecord4.xml


Workflow Example:

	apic1#
	apic1# bash
	admin@apic1:~> icurl 'http://localhost:7777/api/class/aaaModLR.xml?order-by=aaaModLR.created|desc&page-size=100000' > aaaModLR.xml
	  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
									 Dload  Upload   Total   Spent    Left  Speed
	100 8308k  100 8308k    0     0  4313k      0  0:00:01  0:00:01 --:--:-- 4311k
	admin@apic1:~>
	admin@apic1:~> python3 section_parser.py --xml --file aaaModLR.xml --sort created --retro --month --space | more
	2020 Apr 03 17:09:24.947 admin %uni/backupst/snapshots-[uni/fabric/configexp-Daily...: ""Snapshot run-2020-04-03T17-09-23 created"" == name:run-2020-04-03T17-09-23, retire:no

	2020 Apr 03 17:16:39.438 admin %uni/fabric/recovery: ""FabricRecovery created"" == enable:yes

	2020 Apr 03 17:23:11.575 admin %uni/fabric/configimp-myImport: ""ImportP myImport created"" == adminSt:untriggered, failOnDecryptErrors:yes, fileName:unknown.tgz, importMode:atomic, importType:merge, name:myImport, snapshot:yes

	2020 Apr 03 17:23:23.917 admin %uni/fabric/configimp-myImport: ""ImportP myImport modified"" == fileName (Old: unknown.tgz, New: ce2_DailyAutoBackup-2020-04-03T09-00-29.tar.gz)

	2020 Apr 03 17:23:26.199 admin %uni/fabric/configimp-myImport: ""ImportP myImport modified"" == importType (Old: merge, New: replace)

	2020 Apr 03 17:23:32.003 admin %uni/fabric/configimp-myImport/rsRemotePath: ""RsRemotePath created"" == tnFileRemotePathName:BS
	2020 Apr 03 17:23:32.003 admin %uni/fabric/configimp-myImport: ""ImportP myImport modified"" == snapshot (Old: yes, New: no)
	2020 Apr 03 17:23:32.003 admin %uni/fabric/configimp-myImport/rsImportSource: ""RsImportSource created"" == tnFileRemotePathName:BS