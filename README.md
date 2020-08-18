# section_parser

Examples:


python3 section_parser.py --xml --file aaaModLR.xml --sort created >> parsed_aaa.txt
python3 section_parser.py --xml --file aaaModLR.xml --sort created --retro --space  >> retro_aaa.txt
python3 section_parser.py --json --file eventRecord.json --sort created --retro --full >> retro_full_events.txt


Traditional section parser worsk with JSON and XML, and you can sort on any field in the object.

The retro option tries to mimic NXOS logs and will condense most info down to one line. The DN part of the log
will be truncated to 40 characters to conserver space in the line.  This is on by default. It also
has the following options:

--month  >> convert decimal months to alphabetical months
--full   >> prints the full DN (no longer truncated at 40 characters)
--space  >> adds a space when there is a 5 second gap in outputs. This is useful for aaaModLR logs,
            as a single command from the GUI can generate many lines in the aaa logs.  This option
            makes the single configuration changes more noticeable.
 


