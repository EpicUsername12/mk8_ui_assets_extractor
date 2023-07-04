const MSBT = require("msbt.js");
const fs = require("fs");

const languages = {
	// cn: "Chinese ZH-CN 1", (Issues with this language...)
	ed: "Dutch",
	ee: "English (UK)",
	ef: "French (France)",
	eg: "German",
	ei: "Italian",
	ep: "Portugese",
	er: "Russian",
	es: "Spanish (Europe)",
	jp: "Japanese",
	// kr: "Korean", (Issues with this language...)
	// tw: "Chinese ZH-CN 2", (Issues with this language...)
	ue: "English (US)",
	uf: "French (Canada)",
	us: "Spanish (America)",
};

const characters_str =
	"Mario ,Luigi ,Peach ,Daisy ,Yoshi ,Kinopio ,Kinopico ,Nokonoko,Koopa ,DK ,Wario ,Waluigi ,Rosetta ,MetalMario ,MetalPeach ,Jugem ,Heyho ,BbMario ,BbLuigi ,BbPeach ,BbDaisy ,BbRosetta ,Larry ,Lemmy ,Wendy ,Ludwig ,Iggy ,Roy ,Morton ,Mii ,TanukiMario ,Link ,AnimalBoyA ,Shizue ,CatPeach ,HoneKoopa ,AnimalGirlA";

const characters_list = characters_str.split(",");
for (let i = 0; i < characters_list.length; i++) {
	characters_list[i] = characters_list[i].replace(" ", "");
}

const characters_text_ids = [
	1001, // Mario
	1002, // Luigi
	1003, // Peach
	1013, // Daisy
	1004, // Yoshi
	1007, // Toad (Kinopio)
	1021, // Toadette (Kinopico)
	1008, // Koopa (Nokonoko)
	1005, // Bowser (Koopa)
	1006, // Donkey Kong (DK)
	1014, // Wario
	1015, // Waluigi
	1016, // Rosalina (Rosetta)
	1019, // Metal Mario (MetalMario)
	1022, // Pink Gold Peach (MetalPeach)
	1018, // Lakitu (Jugem)
	1017, // Shy Guy (Heyho)
	1009, // Baby Mario (BbMario)
	1010, // Baby Luigi (BbLuigi)
	1011, // Baby Peach (BbPeach)
	1012, // Baby Daisy (BbDaisy)
	1030, // Baby Rosalina (BbRosetta)
	1023, // Larry
	1028, // Lemmy
	1025, // Wendy
	1029, // Ludwig
	1026, // Iggy
	1027, // Roy
	1024, // Morton
	1020, // Mii
	1031, // Tanooki Mario (TanukiMario)
	1034, // Link
	1035, // Villager Boy (AnimalBoyA)
	1036, // Isabelle (Shizue)
	1032, // Cat Peach (CatPeach)
	1033, // Dry Bowser (HoneKoopa)
	1053, // Village Girl (AnimalGirlA)
];

const body_text_ids = {
	K_Std: [0, 1101],
	K_Skl: [1, 1102],
	K_Ufo: [2, 1104],
	K_Sbm: [3, 1105],
	K_Cat: [4, 1106],
	K_Fml: [5, 1107],
	K_Tri: [6, 1108],
	K_Wld: [7, 1109],
	K_Pch: [8, 1110],
	K_Ten: [9, 1111],
	K_Shp: [10, 1112],
	K_Snk: [11, 1113],
	K_Spo: [12, 1115],
	K_Gld: [13, 1114],
	B_Std: [14, 1151],
	B_Fro: [15, 1153],
	B_Mgp: [16, 1154],
	B_Big: [17, 1155],
	B_Amb: [18, 1156],
	B_Mix: [19, 1157],
	B_Kid: [20, 1158],
	B_Jet: [21, 1159],
	B_Ysi: [22, 1160],
	V_Atv: [23, 1181],
	V_Hnc: [24, 1182],
	V_Bea: [25, 1183],
	K_Gla: [26, 1116],
	K_Slv: [27, 1117],
	K_Rst: [28, 1118],
	K_Bfl: [29, 1119],
	K_Tnk: [30, 1120],
	K_Bds: [31, 1121],
	B_Zlb: [32, 1122],
	K_A00: [33, 1101], // Unknown
	K_A01: [34, 1101], // Unknown
	K_Btl: [35, 1123],
	K_Pwc: [36, 1124],
	B_Sct: [37, 1161],
	V_Drb: [38, 1184],
};

const tire_str =
	"Std ,Big ,Sml ,Rng ,Slk ,Mtl ,Btn ,Ofr ,Spg ,Wod ,Fun ,Zst ,Zbi ,Zsm ,Zrn ,Zsl ,Zof ,Gld ,Gla ,Tri ,Anm";
const tire_list = tire_str.split(",");
for (let i = 0; i < tire_list.length; i++) {
	tire_list[i] = tire_list[i].replace(" ", "");
}

const glider_text_ids = {
	G_Std: [0, 1251],
	G_Jgm: [1, 1252],
	G_Wlo: [2, 1253],
	G_Zng: [3, 1254],
	G_Umb: [4, 1255],
	G_Prc: [5, 1257],
	G_Prf: [6, 1258],
	G_Flw: [7, 1259],
	G_Kpa: [8, 1260],
	G_Spl: [9, 1256],
	G_Ptv: [10, 1262],
	G_Gld: [11, 1261],
	G_Hyr: [12, 1263],
	G_Pap: [13, 1264],
};

Object.keys(languages).forEach((language) => {
	console.log(
		`Extracting texts for the following language: ${languages[language]}`
	);

	let msbt = new MSBT(`ui/${language}/Common.msbt`);

	function get_msg_by_id(idx) {
		let key = Object.keys(msbt.nli1).find((k) => k == idx);
		return msbt.txt2.messages[msbt.nli1[key]];
	}

	let lang_chara = {};
	characters_text_ids.forEach((text_id, idx) => {
		lang_chara[characters_list[idx]] = get_msg_by_id(text_id);
	});

	let lang_body = {};
	Object.keys(body_text_ids).forEach((name) => {
		let text_id = body_text_ids[name][1];
		if (text_id == 1117) {
			lang_body[name] = "W 25 Silver Arrow";
		} else {
			lang_body[name] = get_msg_by_id(text_id);
		}
	});

	let lang_tire = {};
	tire_list.forEach((name, idx) => {
		lang_tire["T_" + name] = get_msg_by_id(1201 + idx);
	});

	let lang_gliders = {};
	Object.keys(glider_text_ids).forEach((name) => {
		let text_id = glider_text_ids[name][1];
		lang_gliders[name] = get_msg_by_id(text_id);
	});

	if (!fs.existsSync("locales/")) {
		fs.mkdirSync("locales/");
	}


	fs.writeFileSync(
		`locales/${language}.json`,
		JSON.stringify({ ...lang_chara, ...lang_body, ...lang_tire, ...lang_gliders }, undefined, 4)
	);
});
