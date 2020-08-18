# section_parser

Examples:

	python3 section_parser.py --xml --file aaaModLR.xml --sort created >> parsed_aaa.txt
	python3 section_parser.py --xml --file aaaModLR.xml --sort created --retro --space  >> retro_aaa.txt
	python3 section_parser.py --json --file eventRecord.json --sort created --retro --full >> retro_full_events.txt


Traditional section parser works with JSON and XML, and you can sort on any field in the object.

The retro option tries to mimic NXOS/IOS logs and will condense most info down to one line. The DN part of the log
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


Standard Workflow Example:

	admin@apic1:~> icurl 'http://localhost:7777/api/class/aaaModLR.xml?order-by=aaaModLR.created|desc&page-size=1000' > aaaModLR.xml
	  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
									 Dload  Upload   Total   Spent    Left  Speed
	100  482k  100  482k    0     0  1289k      0 --:--:-- --:--:-- --:--:-- 1285k
	admin@apic1:~>
	admin@apic1:~> python3 section_parser.py --xml --file aaaModLR.xml --sort created | more
	# aaaModLR
	affected        : uni/tn-A/ap-A/epg-A_154/rspathAtt-[topology/pod-1/paths-102/pathep-[eth1/10]]
	cause           : transition
	changeSet       :
	childAction     :
	clientTag       :
	code            : E4212025
	created         : 2020-05-29T16:30:45.066+00:00
	descr           : RsPathAtt topology/pod-1/paths-102/pathep-[eth1/10] deleted
	dn              : subj-[uni/tn-A/ap-A/epg-A_154/rspathAtt-[topology/pod-1/paths-102/pathep-[eth1/10]]]/mod-4294982965
	id              : 4294982965
	ind             : deletion
	modTs           : never
	sessionId       : duyK0fq0S/GEk+pA==
	severity        : info
	status          :
	trig            : config
	txId            : 5765202
	user            : admin

	# aaaModLR
	affected        : uni/tn-A/ap-A/epg-A_112/rspathAtt-[topology/pod-1/paths-102/pathep-[eth1/10]]
	cause           : transition
	changeSet       :
	childAction     :
	clientTag       :
	code            : E4212025
	created         : 2020-05-29T16:30:45.066+00:00
	descr           : RsPathAtt topology/pod-1/paths-102/pathep-[eth1/10] deleted
	dn              : subj-[uni/tn-A/ap-A/epg-A_112/rspathAtt-[topology/pod-1/paths-102/pathep-[eth1/10]]]/mod-4294980281
	id              : 4294980281
	ind             : deletion
	modTs           : never
	sessionId       : duyK0fq0S/A==
	severity        : info
	status          :
	trig            : config
	txId            : 57646085202
	user            : admin

Retro AAA Workflow Example:

	apic1#
	apic1# bash
	admin@apic1:~> icurl 'http://localhost:7777/api/class/aaaModLR.xml?order-by=aaaModLR.created|desc&page-size=100000' > aaaModLR.xml
	  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
									 Dload  Upload   Total   Spent    Left  Speed
	100 8308k  100 8308k    0     0  4313k      0  0:00:01  0:00:01 --:--:-- 4311k
	admin@apic1:~>
	admin@apic1:~> python3 section_parser.py --xml --file aaaModLR.xml --sort created --retro --month --space | more
	2020 Apr 03 17:09:24.947 admin %uni/backupst/snapshots-[uni/fabric/configexp-Daily...: ""Snapshot run-2020-04-03T17-09-23 created"" == name:run-2020-04-03T17-09-23, retire:no

	2020 Apr 03 17:23:11.575 admin %uni/fabric/configimp-myImport: ""ImportP myImport created"" == adminSt:untriggered, failOnDecryptErrors:yes, fileName:unknown.tgz, importMode:atomic, importType:merge, name:myImport, snapshot:yes

	2020 Apr 03 17:23:23.917 admin %uni/fabric/configimp-myImport: ""ImportP myImport modified"" == fileName (Old: unknown.tgz, New: ce2_DailyAutoBackup-2020-04-03T09-00-29.tar.gz)

	2020 Apr 03 17:23:26.199 admin %uni/fabric/configimp-myImport: ""ImportP myImport modified"" == importType (Old: merge, New: replace)

	2020 Apr 03 17:23:32.003 admin %uni/fabric/configimp-myImport/rsRemotePath: ""RsRemotePath created"" == tnFileRemotePathName:BS
	2020 Apr 03 17:23:32.003 admin %uni/fabric/configimp-myImport: ""ImportP myImport modified"" == snapshot (Old: yes, New: no)
	2020 Apr 03 17:23:32.003 admin %uni/fabric/configimp-myImport/rsImportSource: ""RsImportSource created"" == tnFileRemotePathName:BS
	
	
Regex Option Workflow Example:

	admin@apic1:~> python3 section_parser.py --xml --file aaaModLR.xml --regex "BD-A" --sort created --retro | more
	2020-04-03 17:23:50.263 admin %uni/tn-qualys/BD-A/rsigmpsn: ""RsIgmpsn created""
	2020-04-03 17:23:50.263 admin %uni/tn-qualys/BD-A/rsBDToNdP: ""RsBDToNdP created""
	2020-04-03 17:23:50.263 admin %uni/tn-qualys/BD-A/subnet-[10.13.1.1/24]: ""Subnet 10.13.1.1/24 created"" == ip:10.13.1.1/24, preferred:yes, scope:public,shared, virtual:no
	2020-04-03 17:23:50.263 admin %uni/tn-qualys/BD-A/rsbdToEpRet: ""RsBdToEpRet created"" == resolveAct:resolve
	2020-04-03 17:23:50.263 admin %uni/tn-qualys/BD-A: ""BD A created"" == OptimizeWanBandwidth:no, arpFlood:no, epClear:no, intersiteBumTrafficAllow:no, intersiteL2Stretch:no, ipLearning:yes, limitIpLearnToSubnets:yes, llAddr:::, mac:00:22:BD:F8:19:FF, mcastAllow:no, multiDstPktAct:bd-flood, name:A, type:regular, unicastRoute:yes, unkMacUcastAct:proxy, unkMcastAct:flood, vmac:not-applicable
	2020-04-03 17:23:50.263 admin %uni/tn-qualys/BD-A/rsBDToProfile: ""RsBDToProfile created"" == tnL3extOutName:out1, tnRtctrlProfileName:default-export
	2020-04-03 17:23:50.263 admin %uni/tn-qualys/BD-A/subnet-[10.13.1.1/24]/rsBDSubne...: ""RsBDSubnetToProfile created"" == tnL3extOutName:out1
	2020-04-03 17:23:50.263 admin %uni/tn-qualys/BD-A/rsBDToOut-out1: ""RsBDToOut out1 created"" == tnL3extOutName:out1
	2020-04-03 17:23:50.263 admin %uni/tn-qualys/BD-A/rsctx: ""RsCtx created"" == tnFvCtxName:Red
	

Multiple Input File Workflow Example:

	admin@apic1:~> icurl 'http://localhost:7777/api/class/aaaModLR.xml?order-by=aaaModLR.created|desc&page-size=100' > aaaModLR.xml
	  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
									 Dload  Upload   Total   Spent    Left  Speed
	100 53672  100 53672    0     0   200k      0 --:--:-- --:--:-- --:--:--  200k
	admin@apic1:~> icurl 'http://localhost:7777/api/class/aaaModLR.xml?order-by=aaaModLR.created|desc&page-size=100&page=2' > aaaModLR2.xml
	  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
									 Dload  Upload   Total   Spent    Left  Speed
	100 50460  100 50460    0     0   137k      0 --:--:-- --:--:-- --:--:--  137k
	admin@apic1:~> icurl 'http://localhost:7777/api/class/aaaModLR.xml?order-by=aaaModLR.created|desc&page-size=100&page=3' > aaaModLR3.xml
	  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
									 Dload  Upload   Total   Spent    Left  Speed
	100 53472  100 53472    0     0   155k      0 --:--:-- --:--:-- --:--:--  155k


	admin@apic1:~> python3 section_parser.py --xml --file aaaModLR.xml aaaModLR2.xml aaaModLR3.xml --sort created --retro | more
	2020-06-04 19:24:51.668 admin %uni/infra/accportprof-leaf101/hports-pea_101_1_1-t...: ""HPortS pea_101_1_1 range deleted""
	2020-06-04 19:24:51.668 admin %uni/infra/accportprof-leaf101/hports-pea_101_1_1-t...: ""PortBlk block2 deleted""
	2020-06-04 19:25:22.061 admin %uni/infra/accportprof-vpc_1012/hports-cisco_vpc4...: ""HPortS cisco_vpc42 range created"" == name:cisco_vpc42, type:range
	2020-06-04 19:25:22.062 admin %uni/infra/accportprof-vpc_1012/hports-cisco_vpc4...: ""RsAccBaseGrp created"" == fexId:101, tDn:uni/infra/funcprof/accbundle-VPC_42
	2020-06-04 19:25:22.062 admin %uni/infra/accportprof-vpc_1012/hports-cisco_vpc4...: ""PortBlk block2 created"" == fromCard:1, fromPort:1, name:block2, toCard:1, toPort:1
	2020-06-04 19:25:42.514 admin %uni/tn-cisco: ""Tenant cisco created"" == name:cisco
	2020-06-04 19:25:42.514 admin %uni/tn-cisco/rsTenantMonPol: ""RsTenantMonPol created""
	2020-06-04 19:25:42.514 admin %uni/tn-cisco/svcCont: ""SvcCont created""
	2020-06-04 19:25:53.714 admin %uni/tn-cisco/ap-AP: ""Ap AP created"" == name:AP, prio:unspecified
	2020-06-04 19:26:25.546 admin %uni/tn-cisco/ctx-cisco: ""Ctx Cisco created"" == bdEnforcedEnable:no, ipDataPlaneLearning:enabled, knwMcastAct:permit, name:cisco, pcEnfDir:ingress, pcEnfPref:enforced
	2020-06-04 19:26:25.546 admin %uni/tn-cisco/ctx-cisco/rsctxToEpRet: ""RsCtxToEpRet created""
	2020-06-04 19:26:25.546 admin %uni/tn-cisco/ctx-cisco/rsbgpCtxPol: ""RsBgpCtxPol created""
		