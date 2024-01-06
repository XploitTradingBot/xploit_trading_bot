fiat_set = {
    'AUD',
    'CAD',
    'CHF',
    'CNH',
    'CZK',
    'DKK',
    'EUR',
    'GBP',
    'HKD',
    'HUF',
    'INR',
    'JPY',
    'MXN',
    'NOK',
    'NZD',
    'PLN',
    'SAR',
    'SEK',
    'SGD',
    'THB',
    'TRY',
    'USD',
    'XAG',
    'XAU',
    'ZAR',
    'CNY',
}

# tokens to be considered, too many small coins will lead to inefficient trading
token_set = {
    'ABT',
    'ABY',
    'ABYSS',
    'ACAT',
    'ACT',
    'ADA',
    'ADB',
    'ADT',
    'ADX',
    'AE',
    'AEON',
    'AERGO',
    'AGI',
    'AID',
    'AION',
    'AIX',
    'AKRO',
    'ALGO',
    'AMB',
    'AMP',
    'ANKR',
    'ANT',
    'AOA',
    'APH',
    'APPC',
    'ARDR',
    'ARK',
    'ARN',
    'ARPA',
    'ART',
    'ARY',
    'AST',
    'ATOM',
    'AVA',
    'AXPR',
    'BAT',
    'BAX',
    'BAY',
    'BCD',
    'BCH',
    'BCN',
    'BCPT',
    'BFT',
    'BGBP',
    'BITB',
    'BITCNY',
    'BKX',
    'BLK',
    'BLOC',
    'BLOCK',
    'BLT',
    'BLZ',
    'BNB',
    'BNT',
    'BNTY',
    'BOLT',
    'BORA',
    'BOS',
    'BOXX',
    'BPT',
    'BRD',
    'BRK',
    'BRX',
    'BRZ',
    'BSD',
    'BSV',
    'BTC',
    'BTCB',
    'BTCP',
    'BTG',
    'BTM',
    'BTS',
    'BTT',
    'BTU',
    'BU',
    'BURST',
    'BWX',
    'CAG',
    'CAN',
    'CANN',
    'CAPP',
    'CBC',
    'CDT',
    'CELR',
    'CHAT',
    'CHP',
    'CHR',
    'CHSB',
    'CHZ',
    'CLOAK',
    'CMCT',
    'CMT',
    'CND',
    'COCOS',
    'COFI',
    'COS',
    'COSM',
    'COTI',
    'COV',
    'COVAL',
    'CPC',
    'CPT',
    'CRO',
    'CRPT',
    'CRW',
    'CS',
    'CSP',
    'CTXC',
    'CURE',
    'CV',
    'CVC',
    'CXO',
    'DACC',
    'DADI',
    'DAG',
    'DAI',
    'DAPPT',
    'DASH',
    'DAT',
    'DATA',
    'DATX',
    'DBC',
    'DCC',
    'DCR',
    'DCT',
    'DEB',
    'DENT',
    'DERO',
    'DGB',
    'DGD',
    'DLT',
    'DMD',
    'DMT',
    'DNT',
    'DOCK',
    'DOGE',
    'DOPE',
    'DRGN',
    'DTA',
    'DTB',
    'DUSK',
    'DX',
    'DYN',
    'EBST',
    'EBTC',
    'EDG',
    'EDN',
    'EDO',
    'EDR',
    'EFL',
    'EGC',
    'EGT',
    'ELA',
    'ELEC',
    'ELF',
    'EMC',
    'ENG',
    'ENJ',
    'ENQ',
    'ENRG',
    'EOS',
    'ERD',
    'ETC',
    'ETH',
    'ETN',
    'EVX',
    'EXCL',
    'EXP',
    'EXY',
    'FCT',
    'FET',
    'FKX',
    'FLDC',
    'FLIXX',
    'FLO',
    'FOTA',
    'FSN',
    'FTC',
    'FTM',
    'FUEL',
    'FUN',
    'FX',
    'FXC',
    'GAM',
    'GAME',
    'GAS',
    'GAT',
    'GBG',
    'GBYTE',
    'GEO',
    'GLA',
    'GLC',
    'GMB',
    'GNO',
    'GNT',
    'GO',
    'GOD',
    'GOLOS',
    'GRC',
    'GRIN',
    'GRS',
    'GTO',
    'GUP',
    'GVT',
    'HC',
    'HEDG',
    'HINT',
    'HKN',
    'HMQ',
    'HOT',
    'HPB',
    'HST',
    'HXRO',
    'HYDRO',
    'ICN',
    'ICX',
    'IGNIS',
    'IHT',
    'INCNT',
    'ING',
    'INS',
    'IOC',
    'IOG',
    'ION',
    'IOP',
    'IOST',
    'IOTX',
    'ITC',
    'JAR',
    'JNT',
    'KAT',
    'KCS',
    'KEY',
    'KICK',
    'KMD',
    'KNC',
    'KORE',
    'LA',
    'LALA',
    'LAMB',
    'LBA',
    'LBC',
    'LEND',
    'LINK',
    'LOC',
    'LOKI',
    'LOL',
    'LOOM',
    'LRC',
    'LSK',
    'LTC',
    'LUN',
    'LUNA',
    'LYM',
    'MAID',
    'MAN',
    'MANA',
    'MATIC',
    'MCO',
    'MCT',
    'MDA',
    'MEDX',
    'MEME',
    'MER',
    'MET',
    'META',
    'MFT',
    'MHC',
    'MITH',
    'MKR',
    'MLN',
    'MOBI',
    'MOC',
    'MOD',
    'MONA',
    'MORE',
    'MTC',
    'MTH',
    'MTL',
    'MTN',
    'MTV',
    'MUE',
    'MUSIC',
    'MVP',
    'MWAT',
    'NANO',
    'NAS',
    'NAV',
    'NCASH',
    'NEBL',
    'NEO',
    'NEOS',
    'NGC',
    'NIM',
    'NIX',
    'NKN',
    'NLG',
    'NMR',
    'NOIA',
    'NPXS',
    'NRG',
    'NULS',
    'NUSD',
    'NXC',
    'NXS',
    'NXT',
    'OAX',
    'OCEAN',
    'OCN',
    'ODE',
    'OGO',
    'OK',
    'OLT',
    'OMG',
    'OMNI',
    'OMX',
    'ONE',
    'ONG',
    'ONION',
    'ONOT',
    'ONT',
    'OPEN',
    'OPQ',
    'OPT',
    'ORBS',
    'OST',
    'PAL',
    'PARETO',
    'PART',
    'PAX',
    'PAY',
    'PERL',
    'PHX',
    'PI',
    'PINK',
    'PIVX',
    'PLA',
    'PLAY',
    'PMA',
    'POA',
    'POE',
    'POLL',
    'POLY',
    'POT',
    'POWR',
    'PPC',
    'PPT',
    'PRL',
    'PRO',
    'PROM',
    'PTON',
    'PTOY',
    'PXL',
    'QKC',
    'QLC',
    'QNT',
    'QRL',
    'QSP',
    'QTUM',
    'QWARK',
    'R',
    'RADS',
    'RBTC',
    'RCN',
    'RDD',
    'RDN',
    'REN',
    'REP',
    'REQ',
    'RFR',
    'RHOC',
    'RIF',
    'RLC',
    'RVN',
    'RVR',
    'SALT',
    'SBD',
    'SC',
    'SEQ',
    'SERO',
    'SERV',
    'SHIFT',
    'SIB',
    'SKY',
    'SLR',
    'SLS',
    'SLT',
    'SNC',
    'SNGLS',
    'SNM',
    'SNOV',
    'SNT',
    'SNTR',
    'SNX',
    'SOLVE',
    'SOUL',
    'SPC',
    'SPF',
    'SPHR',
    'SPHTX',
    'SPIN',
    'SPND',
    'SPRK',
    'SRN',
    'STEEM',
    'STORJ',
    'STORM',
    'STPT',
    'STQ',
    'STRAT',
    'SUB',
    'SUSD',
    'SWIFT',
    'SWT',
    'SYNX',
    'SYS',
    'TEL',
    'TEMCO',
    'TFD',
    'TFL',
    'TFUEL',
    'THC',
    'THETA',
    'TIME',
    'TIO',
    'TIX',
    'TKS',
    'TKY',
    'TMT',
    'TNB',
    'TNT',
    'TOKO',
    'TOMO',
    'TRAC',
    'TRIG',
    'TRIO',
    'TRST',
    'TRTL',
    'TRX',
    'TSHP',
    'TT',
    'TTC',
    'TUBE',
    'TUSD',
    'TX',
    'UBQ',
    'UKG',
    'UP',
    'UPP',
    'URAC',
    'USDC',
    'USDS',
    'USDT',
    'USE',
    'UT',
    'UTK',
    'VBK',
    'VDX',
    'VEE',
    'VEN',
    'VET',
    'VIA',
    'VIB',
    'VIBE',
    'VID',
    'VITE',
    'VNX',
    'VOL',
    'VRC',
    'VRM',
    'VSYS',
    'VTC',
    'VTHO',
    'WABI',
    'WAN',
    'WAVES',
    'WGP',
    'WIB',
    'WIN',
    'WINGS',
    'WPR',
    'WTC',
    'WXT',
    'XAS',
    'XCP',
    'XDN',
    'XEL',
    'XEM',
    'XHV',
    'XLM',
    'XLR',
    'XMG',
    'XMR',
    'XMY',
    'XNK',
    'XRP',
    'XST',
    'XTZ',
    'XVG',
    'XWC',
    'XYO',
    'XZC',
    'YOYOW',
    'ZCL',
    'ZEC',
    'ZEN',
    'ZIL',
    'ZINC',
    'ZPT',
    'ZRX'
}
