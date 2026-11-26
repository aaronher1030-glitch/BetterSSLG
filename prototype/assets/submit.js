/* Submission form: builds the JSON record in the browser.
   No network, no storage, no dependencies. */
(function () {
  var form = document.getElementById("record-form");
  if (!form) return;

  var preview = document.getElementById("preview");
  var statusBox = document.getElementById("status");
  var regionNames = {
    "I": "Ilocos Region", "II": "Cagayan Valley", "III": "Central Luzon",
    "IV-A": "CALABARZON", "IV-B": "MIMAROPA", "V": "Bicol Region",
    "VI": "Western Visayas", "VII": "Central Visayas", "VIII": "Eastern Visayas",
    "IX": "Zamboanga Peninsula", "X": "Northern Mindanao", "XI": "Davao Region",
    "XII": "SOCCSKSARGEN", "XIII": "Caraga", "NCR": "National Capital Region",
    "CAR": "Cordillera", "BARMM": "Bangsamoro"
  };
  var labels = {
    activities: "Activity", documents: "Issuance",
    reports: "Published report", clubs: "Club"
  };
  var templates = {
    activities: document.getElementById("tpl-activity"),
    documents: document.getElementById("tpl-document"),
    reports: document.getElementById("tpl-report"),
    clubs: document.getElementById("tpl-club")
  };

  function val(el) { return (el.value || "").trim(); }

  function topValue(path) {
    var el = form.querySelector('[data-top="' + path + '"]');
    if (!el) return "";
    return el.type === "checkbox" ? el.checked : val(el);
  }

  function setTop(path, value) {
    var el = form.querySelector('[data-top="' + path + '"]');
    if (!el) return;
    if (el.type === "checkbox") el.checked = !!value;
    else el.value = value == null ? "" : value;
  }

  function listFor(name) {
    return form.querySelector('[data-list="' + name + '"]');
  }

  function rows(name) {
    return Array.prototype.slice.call(listFor(name).querySelectorAll("[data-repeat]"));
  }

  function renumber(name) {
    rows(name).forEach(function (row, i) {
      var label = row.querySelector(".row-head span");
      if (label) label.textContent = labels[name] + " " + (i + 1);
    });
  }

  function addRow(name, data) {
    var node = templates[name].content.firstElementChild.cloneNode(true);
    if (data) {
      Object.keys(data).forEach(function (key) {
        var field = node.querySelector('[data-f="' + key + '"]');
        if (field && data[key] != null) field.value = data[key];
      });
    }
    listFor(name).appendChild(node);
    renumber(name);
    update();
    return node;
  }

  function clearRows(name) {
    listFor(name).innerHTML = "";
  }

  function rowData(row) {
    var out = {};
    Array.prototype.slice.call(row.querySelectorAll("[data-f]")).forEach(function (field) {
      out[field.getAttribute("data-f")] = val(field);
    });
    return out;
  }

  function slugify(text) {
    return text.toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "school";
  }

  function pad(n) { return ("00" + n).slice(-3); }

  function officers() {
    return topValue("sslg.roles").split("\n").map(function (line) {
      return line.trim();
    }).filter(Boolean).map(function (role) {
      var match = role.match(/^Grade\s+(\d+)\s+Representative$/i);
      return {
        role: role,
        grade: match ? parseInt(match[1], 10) : null,
        name: null,
        consent: false
      };
    });
  }

  function orNull(value) { return value ? value : null; }

  function build() {
    var short = topValue("school.short");
    var region = topValue("school.region");
    var term = topValue("sslg.term");
    var yearMatch = term.match(/\d{4}/);
    var year = yearMatch ? yearMatch[0] : String(new Date().getFullYear());

    var activities = rows("activities").map(rowData)
      .filter(function (a) { return a.title || a.date; })
      .map(function (a, i) {
        return {
          id: "AP_SSLG_" + year + "_" + pad(i + 1),
          title: a.title,
          date: a.date || null,
          status: a.status || "completed",
          kind: a.kind || "Activity",
          summary: a.summary || "",
          photo: null
        };
      });

    var documents = rows("documents").map(rowData)
      .filter(function (d) { return d.number || d.title; })
      .map(function (d) {
        return {
          number: d.number,
          series: d.series ? parseInt(d.series, 10) : null,
          type: d.type || "Memorandum",
          direction: d.direction || "issued",
          title: d.title,
          date: d.date || null
        };
      });

    var reports = rows("reports").map(rowData)
      .filter(function (r) { return r.period || r.published; })
      .map(function (r) {
        return {
          period: r.period,
          published: r.published || null,
          type: r.type || "Financial Report"
        };
      });

    var clubs = rows("clubs").map(rowData)
      .filter(function (c) { return c.name; })
      .map(function (c) { return { name: c.name, cluster: c.cluster || "A" }; });

    return {
      slug: slugify(short),
      status: "demo",
      verified_on: null,
      updated: new Date().toISOString().slice(0, 10),
      school: {
        name: topValue("school.name"),
        short: short,
        school_id: topValue("school.school_id"),
        division: topValue("school.division"),
        region: region,
        region_name: regionNames[region] || "",
        cluster: topValue("school.cluster"),
        address: topValue("school.address")
      },
      sslg: {
        term: term,
        adviser: {
          name: null,
          position: topValue("sslg.adviser.position") || "SSLG Adviser",
          consent: false
        },
        contact: orNull(topValue("sslg.contact")),
        facebook: orNull(topValue("sslg.facebook")),
        officers: officers()
      },
      activities: activities,
      documents: documents,
      finance: {
        frequency: topValue("finance.frequency") || "Quarterly",
        reports: reports
      },
      clubs: clubs
    };
  }

  function update() {
    preview.textContent = JSON.stringify(build(), null, 2);
  }

  function say(message, kind) {
    statusBox.textContent = message;
    statusBox.className = "status-msg show " + (kind || "ok");
  }

  function clearStatus() {
    statusBox.className = "status-msg";
    statusBox.textContent = "";
  }

  var required = [
    ["school.name", "the school name"],
    ["school.short", "a short name"],
    ["school.school_id", "the school ID"],
    ["school.division", "the division"],
    ["school.region", "the region"],
    ["school.address", "the town or city"],
    ["sslg.term", "the school year"]
  ];

  function validate() {
    var missing = [];
    form.querySelectorAll(".field.invalid").forEach(function (f) { f.classList.remove("invalid"); });
    required.forEach(function (pair) {
      var el = form.querySelector('[data-top="' + pair[0] + '"]');
      if (!el || !val(el)) {
        missing.push(pair[1]);
        var field = el && el.closest(".field");
        if (field) field.classList.add("invalid");
      }
    });
    if (!topValue("attest")) missing.push("the declaration at the end");
    if (missing.length) {
      say("Before this can be filed: " + missing.join(", ") + ".", "err");
      var first = form.querySelector(".field.invalid input, .field.invalid select");
      if (first) first.focus();
      return false;
    }
    clearStatus();
    return true;
  }

  function download() {
    if (!validate()) return;
    var record = build();
    var text = JSON.stringify(record, null, 2) + "\n";
    var blob = new Blob([text], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = record.slug + ".json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    say("Downloaded " + record.slug + ".json. Send it to your division's SSLG coordinator.", "ok");
  }

  function copy() {
    if (!validate()) return;
    var text = JSON.stringify(build(), null, 2);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        say("Copied. Paste it into an email or a message to your coordinator.", "ok");
      }, function () {
        say("Your browser blocked the clipboard. Use Download instead.", "err");
      });
    } else {
      say("Your browser blocked the clipboard. Use Download instead.", "err");
    }
  }

  var example = {
    school: {
      name: "San Isidro National High School",
      short: "SINHS",
      school_id: "301204",
      division: "Tarlac Province",
      region: "III",
      cluster: "IV",
      address: "San Isidro, Tarlac"
    },
    term: "2026-2027",
    contact: "sslg@sanisidro.example",
    facebook: "facebook.com/sinhs.sslg",
    activities: [
      { title: "Club Fair 2026", date: "2026-06-03", kind: "Program", status: "completed",
        summary: "Recruitment fair for the twelve recognized clubs, with booths grouped by cluster." },
      { title: "Brigada Eskwela 2026", date: "2026-06-08", kind: "Program", status: "completed",
        summary: "Five-day clean-up and repair drive with parents and community partners." },
      { title: "First Quarter General Assembly", date: "2026-08-14", kind: "Meeting", status: "completed",
        summary: "Presentation of the General Plan of Action and the first quarter financial report." }
    ],
    documents: [
      { number: "001", series: "2026", type: "Memorandum", direction: "issued",
        title: "Establishment of LGCC Standing Committees", date: "2026-05-27" },
      { number: "OM-DFSSLG-2026-003", series: "2026", type: "Division Memorandum", direction: "received",
        title: "LGCC Mobilization for Brigada Eskwela 2026", date: "2026-05-18" }
    ],
    reports: [
      { period: "Quarter 1, SY 2026-2027", published: "2026-09-30", type: "Financial Report" }
    ],
    clubs: [
      { name: "Mathematics Club", cluster: "A" },
      { name: "Science Club", cluster: "A" },
      { name: "La Salle Dance Troupe", cluster: "B" },
      { name: "School Chorale", cluster: "B" },
      { name: "Sports Club", cluster: "C" },
      { name: "Red Cross Youth", cluster: "D" }
    ]
  };

  function loadExample() {
    setTop("school.name", example.school.name);
    setTop("school.short", example.school.short);
    setTop("school.school_id", example.school.school_id);
    setTop("school.division", example.school.division);
    setTop("school.region", example.school.region);
    setTop("school.cluster", example.school.cluster);
    setTop("school.address", example.school.address);
    setTop("sslg.term", example.term);
    setTop("sslg.contact", example.contact);
    setTop("sslg.facebook", example.facebook);
    setTop("attest", true);

    clearRows("activities");
    example.activities.forEach(function (a) { addRow("activities", a); });
    clearRows("documents");
    example.documents.forEach(function (d) { addRow("documents", d); });
    clearRows("reports");
    example.reports.forEach(function (r) { addRow("reports", r); });
    clearRows("clubs");
    example.clubs.forEach(function (c) { addRow("clubs", c); });

    update();
    say("Example loaded. Replace every value with your school's before filing.", "ok");
  }

  form.addEventListener("input", update);
  form.addEventListener("change", update);
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    download();
  });

  form.addEventListener("click", function (event) {
    var add = event.target.closest("[data-add]");
    if (add) { addRow(add.getAttribute("data-add")); return; }

    var remove = event.target.closest("[data-remove]");
    if (remove) {
      var row = remove.closest("[data-repeat]");
      var list = remove.closest("[data-list]");
      row.remove();
      if (list) renumber(list.getAttribute("data-list"));
      update();
    }
  });

  document.getElementById("download").addEventListener("click", download);
  document.getElementById("copy").addEventListener("click", copy);
  document.getElementById("example").addEventListener("click", loadExample);

  addRow("activities");
  addRow("clubs");
  update();

  /* Shareable demo link: submit.html#example (or ?example=1) prefills the form. */
  if (location.hash === "#example" || /[?&]example=1/.test(location.search)) loadExample();
})();
