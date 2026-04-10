/* ============================================================
   World Economy Map — app.js  (v2: geographic bubbles + LOD)
   D3 v7 + TopoJSON + us-atlas admin borders
   ============================================================ */

(function () {
  'use strict';

  /* ── Constants ──────────────────────────────────────────── */

  const TOPO_URL    = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json';
  const DATA_URL    = 'regions_economy.json';
  // Natural Earth 110m admin-1 subdivisions (geographic lon/lat — works with any D3 projection).
  // Loaded asynchronously; map renders without it if the fetch fails.
  const ADMIN1_URL  = 'https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@master/geojson/ne_50m_admin_1_states_provinces.geojson';

  const INDUSTRY_COLORS = {
    Extractive:    '#c0392b',
    Agriculture:   '#27ae60',
    Manufacturing: '#2980b9',
    Services:      '#8e44ad',
    Technology:    '#16a085',
    Energy:        '#f39c12',
    Unknown:       '#95a5a6',
  };
  const INDUSTRY_ORDER = [
    'Services', 'Manufacturing', 'Technology',
    'Agriculture', 'Energy', 'Extractive', 'Unknown',
  ];

  const R_MIN  = 4;    // min bubble radius (px at zoom=1)
  const R_MAX  = 24;   // max bubble radius
  const R_NULL = 2.5;  // fixed radius when GDP is null

  // LOD zoom thresholds
  const LOD_COUNTRY_MAX   = 3;   // zoom <= this → only country bubbles visible
  const LOD_REGION_ALL    = 7;   // zoom >= this → all region bubbles fully visible
  const LOD_CONCEAL_START = 12;  // largest GDP region starts fading OUT at this zoom
  const LOD_CONCEAL_END   = 16;  // largest GDP region fully gone at this zoom

  const LEGEND_GDP_VALUES = [10, 100, 500, 2000];
  const LEGEND_PC_VALUES  = [1000, 10000, 50000, 100000];
  const LEGEND_POP_VALUES = [1e6, 10e6, 50e6, 100e6];

  /* ── ISO 3166-1 numeric → canonical country name ────────── */
  const ISO_NUM_TO_NAME = {
    '4':   'Afghanistan',       '8':   'Albania',
    '12':  'Algeria',           '24':  'Angola',
    '32':  'Argentina',         '36':  'Australia',
    '40':  'Austria',           '50':  'Bangladesh',
    '56':  'Belgium',           '64':  'Bhutan',
    '68':  'Bolivia',           '70':  'Bosnia and Herzegovina',
    '76':  'Brazil',            '100': 'Bulgaria',
    '104': 'Myanmar',           '108': 'Burundi',
    '116': 'Cambodia',          '120': 'Cameroon',
    '124': 'Canada',            '132': 'Cabo Verde',
    '140': 'Central African Republic', '144': 'Sri Lanka',
    '148': 'Chad',              '152': 'Chile',
    '156': 'China',             '170': 'Colombia',
    '174': 'Comoros',           '178': 'Republic of the Congo',
    '180': 'Democratic Republic of the Congo', '188': 'Costa Rica',
    '191': 'Croatia',           '192': 'Cuba',
    '196': 'Cyprus',            '203': 'Czechia',
    '208': 'Denmark',           '214': 'Dominican Republic',
    '218': 'Ecuador',           '818': 'Egypt',
    '222': 'El Salvador',       '232': 'Eritrea',
    '233': 'Estonia',           '231': 'Ethiopia',
    '246': 'Finland',           '250': 'France',
    '266': 'Gabon',             '276': 'Germany',
    '288': 'Ghana',             '300': 'Greece',
    '320': 'Guatemala',         '324': 'Guinea',
    '332': 'Haiti',             '340': 'Honduras',
    '348': 'Hungary',           '356': 'India',
    '360': 'Indonesia',         '364': 'Iran',
    '368': 'Iraq',              '372': 'Ireland',
    '376': 'Israel',            '380': 'Italy',
    '388': 'Jamaica',           '392': 'Japan',
    '400': 'Jordan',            '398': 'Kazakhstan',
    '404': 'Kenya',             '408': 'North Korea',
    '410': 'South Korea',       '414': 'Kuwait',
    '418': 'Laos',              '422': 'Lebanon',
    '426': 'Lesotho',           '430': 'Liberia',
    '434': 'Libya',             '440': 'Lithuania',
    '442': 'Luxembourg',        '450': 'Madagascar',
    '454': 'Malawi',            '458': 'Malaysia',
    '466': 'Mali',              '478': 'Mauritania',
    '484': 'Mexico',            '496': 'Mongolia',
    '499': 'Montenegro',        '504': 'Morocco',
    '508': 'Mozambique',        '516': 'Namibia',
    '524': 'Nepal',             '528': 'Netherlands',
    '554': 'New Zealand',       '562': 'Niger',
    '566': 'Nigeria',           '578': 'Norway',
    '586': 'Pakistan',          '591': 'Panama',
    '598': 'Papua New Guinea',  '275': 'Palestine',
    '604': 'Peru',              '608': 'Philippines',
    '616': 'Poland',            '620': 'Portugal',
    '634': 'Qatar',             '642': 'Romania',
    '643': 'Russia',            '646': 'Rwanda',
    '682': 'Saudi Arabia',      '686': 'Senegal',
    '694': 'Sierra Leone',      '703': 'Slovakia',
    '705': 'Slovenia',          '706': 'Somalia',
    '710': 'South Africa',      '728': 'South Sudan',
    '724': 'Spain',             '729': 'Sudan',
    '740': 'Suriname',          '752': 'Sweden',
    '756': 'Switzerland',       '760': 'Syria',
    '762': 'Tajikistan',        '764': 'Thailand',
    '626': 'Timor-Leste',       '768': 'Togo',
    '780': 'Trinidad and Tobago', '788': 'Tunisia',
    '792': 'Turkey',            '834': 'Tanzania',
    '800': 'Uganda',            '804': 'Ukraine',
    '784': 'United Arab Emirates', '826': 'United Kingdom',
    '840': 'United States of America', '858': 'Uruguay',
    '860': 'Uzbekistan',        '862': 'Venezuela',
    '704': 'Vietnam',           '887': 'Yemen',
    '894': 'Zambia',            '716': 'Zimbabwe',
    '51':  'Armenia',           '31':  'Azerbaijan',
    '112': 'Belarus',           '262': 'Djibouti',
    '268': 'Georgia',           '807': 'North Macedonia',
    '417': 'Kyrgyzstan',        '480': 'Mauritius',
    '795': 'Turkmenistan',
  };

  const COUNTRY_ALIASES = {
    'United States':                          'United States of America',
    'USA':                                    'United States of America',
    'US':                                     'United States of America',
    'UK':                                     'United Kingdom',
    'Great Britain':                          'United Kingdom',
    'Republic of Korea':                      'South Korea',
    'Korea':                                  'South Korea',
    "Democratic People's Republic of Korea":  'North Korea',
    'Russian Federation':                     'Russia',
    'Islamic Republic of Iran':               'Iran',
    'Republic of China':                      'Taiwan',
    'Plurinational State of Bolivia':         'Bolivia',
    'Bolivarian Republic of Venezuela':       'Venezuela',
    'United Republic of Tanzania':            'Tanzania',
    'Syrian Arab Republic':                   'Syria',
    "Lao People's Democratic Republic":       'Laos',
    'Lao PDR':                                'Laos',
    'Viet Nam':                               'Vietnam',
    'Czech Republic':                         'Czechia',
    'Congo':                                  'Republic of the Congo',
    'Congo, Rep.':                            'Republic of the Congo',
    'Congo, Dem. Rep.':                       'Democratic Republic of the Congo',
    'DRC':                                    'Democratic Republic of the Congo',
    'DR Congo':                               'Democratic Republic of the Congo',
    'Burma':                                  'Myanmar',
    'Ivory Coast':                            "Côte d'Ivoire",
    'Türkiye':                                'Turkey',
    'Swaziland':                              'Eswatini',
    'Cape Verde':                             'Cabo Verde',
    'Macedonia':                              'North Macedonia',
    'East Timor':                             'Timor-Leste',
    'Palestinian Territory':                  'Palestine',
    'West Bank and Gaza':                     'Palestine',
    'Kyrgyz Republic':                        'Kyrgyzstan',
    'Slovak Republic':                        'Slovakia',
    'Taiwan, Province of China':              'Taiwan',
    'Korea, Republic of':                     'South Korea',
    'Korea, Dem. Rep.':                       'North Korea',
    'Iran, Islamic Republic of':              'Iran',
    'Tanzania, United Republic of':           'Tanzania',
    'Venezuela, RB':                          'Venezuela',
    'Bolivia, Plurinational State of':        'Bolivia',
    'Moldova':                                'Moldova',
    'Republic of Moldova':                    'Moldova',
    'Brunei':                                 'Brunei Darussalam',
    'Republic of Ireland':                    'Ireland',
    'Trinidad & Tobago':                      'Trinidad and Tobago',
    'United States Virgin Islands':           'United States of America',
    'Puerto Rico':                            'United States of America',
    'Hong Kong':                              'China',
    'Macau':                                  'China',
    'Macao':                                  'China',
  };

  /* ── Manual centroid overrides ──────────────────────────────
     Only add entries here for regions where auto-computation
     (via buildAutoCentroids / admin1Index) produces a wrong or
     ocean-falling centroid.  regionName → [lon, lat].
     The automatic system (buildAutoCentroids) handles the rest.  ── */
  const CENTROID_OVERRIDES = {
    // Hawaii: the largest-polygon centroid of the Big Island is fine,
    // but the NE 110m dataset sometimes omits smaller island chains —
    // use a hand-picked central point for the state as a whole.
    'Hawaii':  [-157.50, 20.27],
    // Alaska: centroid of the mainland polygon drifts toward the Aleutians.
    'Alaska':  [-153.37, 64.20],
  };

  /* ── Wikipedia → Natural Earth region name aliases ──────────
     Keys are Wikipedia region names; values are Natural Earth name fields.
     Only list cases where normalisation alone can't resolve the mismatch. ── */
  const REGION_NAME_ALIASES = {
    // China
    'Inner Mongolia':           'Nei Mongol',
    'Tibet':                    'Xizang',
    'Xinjiang':                 'Xinjiang Uygur',
    // Russia
    'Khanty-Mansi Autonomous Okrug': 'Khanty-Mansiyskiy Avtonomnyy Okrug',
    'Yamalo-Nenets Autonomous Okrug': 'Yamalo-Nenetskiy Avtonomnyy Okrug',
    'Chukotka Autonomous Okrug': 'Chukotskiy Avtonomnyy Okrug',
    // India
    'Jammu and Kashmir':        'Jammu and Kashmir',
    'Uttarakhand':              'Uttaranchal',
    // UK
    'England':                  'England',
    'Wales':                    'Wales',
    'Scotland':                 'Scotland',
    'Northern Ireland':         'Northern Ireland',
    // Japan
    'Hyōgo Prefecture':         'Hyogo',
    'Ōsaka Prefecture':         'Osaka',
    'Tōkyō':                    'Tokyo',
    'Hokkaidō':                 'Hokkaido',
    'Kyōto Prefecture':         'Kyoto',
    // US edge cases
    'New York':                 'New York',
  };

  /* ── Application state ──────────────────────────────────── */

  let allRegions        = [];
  let topoData          = null;
  let admin1GeoJSON     = null;  // Natural Earth admin-1 GeoJSON (loaded async)
  let admin1Index       = {};    // countryName → { regionName → { centroid, feature } }
  let autoCentroids     = new Map(); // regionId → [lon, lat] — pre-computed at load time
  let countryCentroids  = {};    // canonical-name → [lon, lat] (largest land mass)
  let countryNameIndex  = {};
  let countryAggregates = [];    // one aggregate entry per country

  let currentMetric     = 'gdp_total';
  let activeIndustries  = new Set(INDUSTRY_ORDER);
  let showUnknownGdp    = false;
  let searchTerm          = '';
  let selectedRegion      = null;
  let selectedCountryId   = null;  // id of country aggregate whose bubble is hidden on selection
  let currentZoom         = 1;

  let svg, gRoot, gAdminBorders, gCountryPaths, gCountryBubbles, gRegionBubbles;
  let projection, pathGen, zoomBehaviour;
  let _rScale = null;

  /* ── DOM refs ───────────────────────────────────────────── */

  const $loadingOverlay   = document.getElementById('loading-overlay');
  const $errorOverlay     = document.getElementById('error-overlay');
  const $errorMsg         = document.getElementById('error-msg');
  const $mapSvg           = document.getElementById('map-svg');
  const $tooltip          = document.getElementById('tooltip');
  const $detailPanel      = document.getElementById('detail-panel');
  const $regionCountBadge = document.getElementById('region-count-badge');
  const $zoomIndicator    = document.getElementById('zoom-indicator');
  const $statVisible      = document.getElementById('stat-visible');
  const $statTotalGdp     = document.getElementById('stat-total-gdp');
  const $searchInput      = document.getElementById('search-input');
  const $searchResults    = document.getElementById('search-results');
  const $industryPillsEl  = document.getElementById('industry-pills');
  const $sizeLegendEl     = document.getElementById('size-legend-circles');

  /* ── Bootstrap ──────────────────────────────────────────── */

  async function init() {
    try {
      const [topo, regions] = await Promise.all([
        fetchJSON(TOPO_URL, 'World map topology'),
        fetchJSON(DATA_URL, 'Economy data'),
      ]);

      topoData   = topo;
      allRegions = cleanRegions(regions);

      _rScale = getUnifiedRScale(currentMetric);

      // Country centroids — placed on largest contiguous land mass
      buildCentroids(topo);
      computeCountryAggregates();

      setupSVG();
      drawBaseMap();       // creates gAdminBorders group (empty until admin-1 loads)
      buildCountryBubbles();
      buildRegionBubbles();
      buildSidebarUI();
      updateLOD(1);
      hideLoading();
      updateStats();

      // Admin-1 GeoJSON is non-critical: load async so initial map is not delayed.
      // When loaded: draw borders + rebuild region bubbles with accurate centroids.
      fetchJSON(ADMIN1_URL, 'Admin-1 boundaries')
        .then(gj => {
          admin1GeoJSON = gj;
          buildAdmin1Index(gj);
          buildAutoCentroids();   // pre-compute centroid map for all regions
          drawAdminBorders();
          buildRegionBubbles();   // reposition with admin-1 centroids where available
          if (!selectedRegion) updateLOD(currentZoom);
        })
        .catch(err => console.warn('[EconomyMap] Admin-1 not loaded:', err.message));

    } catch (err) {
      console.error('[EconomyMap]', err);
      showError(err.message);
    }
  }

  async function fetchJSON(url, label) {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`Failed to fetch ${label}: HTTP ${resp.status} from ${url}`);
    return resp.json();
  }

  /* ── Data cleaning ──────────────────────────────────────── */

  function cleanRegions(raw) {
    if (!Array.isArray(raw)) throw new Error('regions_economy.json must be a JSON array');
    return raw.map((d, i) => {
      const cat = (d.industry_category && INDUSTRY_COLORS[d.industry_category])
        ? d.industry_category : 'Unknown';
      return {
        id:                i,
        country:           d.country  || 'Unknown',
        region:            d.region   || 'Unknown Region',
        wikipedia_url:     d.wikipedia_url || null,
        gdp_total:         validNum(d.gdp_usd_billions),
        gdp_per_capita:    validNum(d.gdp_per_capita_usd),
        gdp_year:          d.gdp_year || null,
        industry_gdp:      (d.industry_gdp_usd_billions && typeof d.industry_gdp_usd_billions === 'object')
                             ? d.industry_gdp_usd_billions : null,
        industry_category: cat,
        primary_industry:  d.primary_industry || null,
        economy_excerpt:   d.economy_excerpt  || null,
        population:        validNum(d.population),
        area_km2:          validNum(d.area_km2),
        unemployment_rate: (typeof d.unemployment_rate === 'number' && isFinite(d.unemployment_rate)) ? d.unemployment_rate : null,
        hdi:               (typeof d.hdi === 'number' && isFinite(d.hdi) && d.hdi > 0) ? d.hdi : null,
        hdi_year:          d.hdi_year || null,
        data_quality:      d.data_quality || 'stub',
      };
    });
  }

  function validNum(v) {
    return (typeof v === 'number' && isFinite(v) && v > 0) ? v : null;
  }

  /* ── Country centroids (from world-atlas) ───────────────── */

  function buildCentroids(topo) {
    const feature = topojson.feature(topo, topo.objects.countries);
    feature.features.forEach(f => {
      const name = ISO_NUM_TO_NAME[String(f.id)];
      if (!name) return;
      // Use centroid of largest contiguous polygon to avoid ocean positions
      // (e.g. US centroid would fall in Pacific if Alaska is included)
      const c = largestPolygonCentroid(f);
      if (c && isFinite(c[0])) {
        countryCentroids[name] = c;
        countryNameIndex[name] = true;
      }
    });
  }

  // Returns the geographic centroid of the largest polygon in a feature.
  // For MultiPolygon countries (US, Russia, Indonesia…) this places the
  // bubble on the main land mass rather than a mathematically correct but
  // geographically misleading centroid (which can fall in the ocean).
  function largestPolygonCentroid(feature) {
    const g = feature.geometry;
    if (!g) return d3.geoCentroid(feature);
    if (g.type === 'Polygon') return d3.geoCentroid(feature);
    if (g.type === 'MultiPolygon') {
      let maxArea = -Infinity, best = null;
      g.coordinates.forEach(coords => {
        const poly = { type: 'Feature', geometry: { type: 'Polygon', coordinates: coords } };
        const area = d3.geoArea(poly);
        if (area > maxArea) { maxArea = area; best = poly; }
      });
      return best ? d3.geoCentroid(best) : d3.geoCentroid(feature);
    }
    return d3.geoCentroid(feature);
  }

  function resolveCentroid(countryName) {
    if (countryCentroids[countryName]) return countryCentroids[countryName];
    const alias = COUNTRY_ALIASES[countryName];
    if (alias && countryCentroids[alias]) return countryCentroids[alias];
    const lower = countryName.toLowerCase();
    for (const [k, v] of Object.entries(countryCentroids)) {
      if (k.toLowerCase() === lower) return v;
    }
    return null;
  }

  /* ── Admin-1 index (from Natural Earth GeoJSON) ────────────
     General-purpose: works for any country in the dataset.
     Called once admin1GeoJSON has loaded (async after init).    ── */

  function buildAdmin1Index(geojson) {
    admin1Index = {};
    geojson.features.forEach(f => {
      const p = f.properties;
      if (!f.geometry || !p) return;

      // Resolve parent country to canonical name
      const rawAdmin = p.admin || p.geonunit || '';
      let canonical = COUNTRY_ALIASES[rawAdmin] || rawAdmin;
      if (!canonical) return;
      // Also try lowercase match against known country centroids
      if (!countryNameIndex[canonical]) {
        const lc = canonical.toLowerCase();
        for (const k of Object.keys(countryCentroids)) {
          if (k.toLowerCase() === lc) { canonical = k; break; }
        }
      }

      if (!admin1Index[canonical]) admin1Index[canonical] = {};

      const centroid = largestPolygonCentroid(f);
      if (!centroid || !isFinite(centroid[0])) return;

      // Index by all available name fields for maximum match coverage
      [p.name, p.name_en, p.name_alt, p.woe_name, p.gn_name]
        .filter(Boolean)
        .forEach(nm => {
          if (!admin1Index[canonical][nm]) {
            admin1Index[canonical][nm] = { centroid, feature: f };
          }
        });
    });
  }

  function getRegionGeo(d) {
    // 1. Manual override (hand-curated entries for known problem regions)
    if (CENTROID_OVERRIDES[d.region]) return CENTROID_OVERRIDES[d.region];

    // 2. Pre-computed auto-centroids (O(1) lookup, built at load time from admin1Index)
    if (autoCentroids.has(d.id)) return autoCentroids.get(d.id);

    // 3. Natural Earth admin-1 live lookup (fallback for any edge cases missed by step 2)
    const canonical = COUNTRY_ALIASES[d.country] || d.country;
    const idx = admin1Index[canonical] || admin1Index[d.country];
    if (idx) {
      if (idx[d.region]) return idx[d.region].centroid;
      const lc = d.region.toLowerCase();
      for (const [k, v] of Object.entries(idx)) {
        if (k.toLowerCase() === lc) return v.centroid;
      }
    }

    // 4. Country centroid fallback (largest land mass)
    return resolveCentroid(d.country);
  }

  /* ── Auto-centroid pre-computation ─────────────────────────
     Called once after buildAdmin1Index() has populated admin1Index.
     Iterates every region in allRegions, reuses the same name-matching
     logic as getRegionGeo() step 3, and caches results in autoCentroids
     (regionId → [lon, lat]) for fast O(1) lookup at render time.      ── */

  // Strip common admin suffixes and parenthetical notes for fuzzy matching.
  // e.g. "Fujian Province" → "Fujian", "Shanxi (province)" → "Shanxi"
  const ADMIN_SUFFIX_RE = /\s+(Province|Prefecture|Oblast|Krai|Okrug|Region|District|County|State|Department|Governorate|Emirate|Canton|Territory|Division|Island|Islands|Circuit|Republic)$/i;
  function normaliseName(s) {
    return s
      .replace(/\s*\([^)]*\)/g, '')      // strip parentheticals
      .replace(ADMIN_SUFFIX_RE, '')       // strip admin suffix
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')  // strip diacritics
      .trim().toLowerCase();
  }

  function buildAutoCentroids() {
    autoCentroids = new Map();
    let matched = 0;
    const unmatched = [];

    allRegions.forEach(d => {
      // Skip if a manual override already covers this region
      if (CENTROID_OVERRIDES[d.region]) return;

      const canonical = COUNTRY_ALIASES[d.country] || d.country;
      const idx = admin1Index[canonical] || admin1Index[d.country];
      if (!idx) { unmatched.push(d); return; }

      // 1. Exact match
      if (idx[d.region]) {
        autoCentroids.set(d.id, idx[d.region].centroid);
        matched++; return;
      }
      // 2. Known alias map
      const alias = REGION_NAME_ALIASES[d.region];
      if (alias && idx[alias]) {
        autoCentroids.set(d.id, idx[alias].centroid);
        matched++; return;
      }
      // 3. Case-insensitive exact
      const lc = d.region.toLowerCase();
      let found = false;
      for (const [k, v] of Object.entries(idx)) {
        if (k.toLowerCase() === lc) {
          autoCentroids.set(d.id, v.centroid); matched++; found = true; break;
        }
      }
      if (found) return;
      // 4. Normalised (suffix-stripped + diacritic-stripped) match
      const normRegion = normaliseName(d.region);
      for (const [k, v] of Object.entries(idx)) {
        if (normaliseName(k) === normRegion) {
          autoCentroids.set(d.id, v.centroid); matched++; found = true; break;
        }
      }
      if (found) return;

      unmatched.push(d);
    });

    unmatched.forEach(d => {
      console.log(`[Centroid] No match: ${d.country} / ${d.region}`);
    });

    const total = allRegions.filter(d => !CENTROID_OVERRIDES[d.region]).length;
    console.log(`[Centroid] Resolved ${matched}/${total} regions from GeoJSON, ${unmatched.length} unmatched`);
  }

  /* ── Country aggregates ─────────────────────────────────── */

  function computeCountryAggregates() {
    const byCountry = d3.group(allRegions, d => d.country);
    countryAggregates = [];
    byCountry.forEach((regions, country) => {
      const geo = resolveCentroid(country);
      if (!geo) return;

      const withGdp  = regions.filter(d => d.gdp_total !== null);
      const gdpTotal = withGdp.length ? d3.sum(withGdp, d => d.gdp_total) : null;

      const withPop  = regions.filter(d => d.population !== null);
      const popTotal = withPop.length ? d3.sum(withPop, d => d.population) : null;

      // Dominant industry by region count (excluding Unknown)
      const catCounts = {};
      regions.forEach(d => { catCounts[d.industry_category] = (catCounts[d.industry_category] || 0) + 1; });
      const domCat = Object.entries(catCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'Unknown';

      const popStr = popTotal ? fmtPop(popTotal) : null;
      const excerptParts = [`${regions.length} regions`, `Dominant sector: ${domCat}`];
      if (popStr) excerptParts.push(`Pop: ${popStr}`);

      countryAggregates.push({
        id:                'ctry_' + country,
        isCountryBubble:   true,
        country,
        region:            country,
        geo,
        gdp_total:         gdpTotal,
        gdp_per_capita:    null,
        gdp_year:          null,
        population:        popTotal,
        area_km2:          null,
        unemployment_rate: null,
        hdi:               null,
        hdi_year:          null,
        data_quality:      gdpTotal ? 'partial' : 'stub',
        industry_gdp:      null,
        industry_category: domCat,
        primary_industry:  null,
        economy_excerpt:   excerptParts.join(' · '),
        wikipedia_url:     null,
        regionCount:       regions.length,
        regions,
      });
    });
  }

  /* ── SVG setup & projection ─────────────────────────────── */

  function getMapSize() {
    return {
      w: $mapSvg.clientWidth  || window.innerWidth  - 280,
      h: $mapSvg.clientHeight || window.innerHeight - 56,
    };
  }

  function setupSVG() {
    const { w, h } = getMapSize();

    projection = d3.geoNaturalEarth1()
      .scale(Math.min(w / 6.28, h / 3.4))
      .translate([w / 2, h / 2]);

    pathGen = d3.geoPath().projection(projection);

    svg = d3.select($mapSvg);
    svg.selectAll('*').remove();

    zoomBehaviour = d3.zoom()
      .scaleExtent([0.4, 25])
      .on('zoom', handleZoom);

    zoomBehaviour.translateExtent([[-w * 0.6, -h * 0.6], [w * 1.6, h * 1.6]]);

    svg.call(zoomBehaviour);
    gRoot = svg.append('g').attr('class', 'map-root');
  }

  function handleZoom(event) {
    const k = event.transform.k;
    currentZoom = k;
    gRoot.attr('transform', event.transform);
    $zoomIndicator.textContent = k.toFixed(2) + '×';

    // Keep strokes visually thin
    gRoot.selectAll('.country-path').attr('stroke-width', 0.5 / k);
    gRoot.selectAll('.graticule').attr('stroke-width', 0.5 / k);
    gRoot.selectAll('.admin-border').attr('stroke-width', 0.4 / k);
    gRoot.selectAll('.bubble circle').attr('stroke-width', 1.2 / k);

    // Drive LOD (only when nothing is selected — selection overrides opacity)
    if (!selectedRegion) updateLOD(k);
  }

  /* ── Base map ───────────────────────────────────────────── */

  function drawBaseMap() {
    // Ocean sphere
    gRoot.append('path')
      .datum({ type: 'Sphere' })
      .attr('class', 'sphere')
      .attr('d', pathGen);

    // Graticule
    gRoot.append('path')
      .datum(d3.geoGraticule()())
      .attr('class', 'graticule')
      .attr('d', pathGen);

    // Country fills — also serve as clickable/hoverable hit areas at national zoom
    const countries = topojson.feature(topoData, topoData.objects.countries);
    gCountryPaths = gRoot.append('g').attr('class', 'country-paths-group');
    gCountryPaths.selectAll('.country-path')
      .data(countries.features)
      .join('path')
        .attr('class', 'country-path')
        .attr('d', pathGen)
        .on('mouseenter', onCountryPathEnter)
        .on('mousemove',  onTooltipMove)
        .on('mouseleave', onTooltipLeave)
        .on('click',      onCountryPathClick);

    // Country border mesh
    gRoot.append('path')
      .datum(topojson.mesh(topoData, topoData.objects.countries, (a, b) => a !== b))
      .attr('fill', 'none')
      .attr('stroke', 'var(--map-border)')
      .attr('stroke-width', 0.5)
      .attr('d', pathGen);

    // Admin-1 borders (currently US states)
    gAdminBorders = gRoot.append('g').attr('class', 'admin-borders-group');
    drawAdminBorders();

    // Bubble layers — drawn above borders
    gCountryBubbles = gRoot.append('g').attr('class', 'country-bubbles-group');
    gRegionBubbles  = gRoot.append('g').attr('class', 'region-bubbles-group');
  }

  function drawAdminBorders() {
    gAdminBorders.selectAll('*').remove();
    if (!admin1GeoJSON) return;

    // Natural Earth GeoJSON uses geographic lon/lat — render directly with pathGen.
    // Only draw borders for countries that appear in our dataset (avoids noise).
    const knownCountries = new Set(
      allRegions.map(d => COUNTRY_ALIASES[d.country] || d.country)
    );
    // Always include both sides of an alias pair
    allRegions.forEach(d => { knownCountries.add(d.country); });

    const relevant = admin1GeoJSON.features.filter(f => {
      const raw = f.properties?.admin || f.properties?.geonunit || '';
      const canonical = COUNTRY_ALIASES[raw] || raw;
      return knownCountries.has(canonical) || knownCountries.has(raw);
    });

    gAdminBorders.selectAll('.admin-border')
      .data(relevant)
      .join('path')
        .attr('class', 'admin-border')
        .attr('d', pathGen)
        .on('mouseenter', onAdminBorderEnter)
        .on('mousemove',  onTooltipMove)
        .on('mouseleave', onTooltipLeave)
        .on('click',      onAdminBorderClick);
  }

  /* ── Unified radius scale ───────────────────────────────────── */
  // Single absolute scale shared by country bubbles, region bubbles, and the
  // size legend — so the key accurately reflects all bubble sizes on screen.

  function getUnifiedRScale(metric) {
    if (metric === 'gdp_total')    return d3.scaleSqrt().domain([1, 25000]).range([R_MIN, R_MAX]).clamp(true);
    if (metric === 'population')   return d3.scaleSqrt().domain([1e5, 2e8]).range([R_MIN, R_MAX]).clamp(true);
    return d3.scaleSqrt().domain([100, 150000]).range([R_MIN, R_MAX]).clamp(true);
  }

  function getBubbleR(d, metric) {
    const v = metric === 'population' ? d.population : d[metric];
    return (v !== null && v > 0) ? _rScale(v) : R_NULL;
  }

  /* ── Country bubbles ────────────────────────────────────── */

  function buildCountryBubbles() {
    const visible = countryAggregates.filter(d => {
      if (!activeIndustries.has(d.industry_category)) return false;
      const metricVal = currentMetric === 'population' ? d.population : d[currentMetric];
      return showUnknownGdp || metricVal !== null;
    });

    gCountryBubbles.selectAll('.country-bubble').remove();

    const grps = gCountryBubbles.selectAll('.country-bubble')
      .data(visible, d => d.id)
      .join('g')
        .attr('class', 'bubble country-bubble')
        .attr('transform', d => {
          const px = projection(d.geo);
          return `translate(${px[0]},${px[1]})`;
        });

    grps.append('circle')
      .attr('r',            d => getBubbleR(d, currentMetric))
      .attr('fill',         d => hexToRgba(INDUSTRY_COLORS[d.industry_category], 0.2))
      .attr('stroke',       d => INDUSTRY_COLORS[d.industry_category])
      .attr('stroke-width', 1.2);
  }

  /* ── Region bubbles ─────────────────────────────────────── */

  function buildRegionBubbles() {
    const visible = getVisibleRegions();

    // Assign revealZoom and concealZoom per region (per-country ranking)
    const byCountry = d3.group(visible, d => d.country);
    const revealMap  = new Map();
    const concealMap = new Map();
    byCountry.forEach((regs) => {
      const metricKey = currentMetric === 'population' ? 'population' : currentMetric;
      const sorted = [...regs].sort((a, b) => (b[metricKey] || 0) - (a[metricKey] || 0));
      const N = sorted.length;
      sorted.forEach((d, i) => {
        // Reveal: largest (i=0) at LOD_COUNTRY_MAX, smallest at LOD_REGION_ALL
        const t = N <= 1 ? 0 : i / (N - 1);
        revealMap.set(d.id, LOD_COUNTRY_MAX + t * (LOD_REGION_ALL - LOD_COUNTRY_MAX));

        // Conceal: top 50% of regions (by GDP) fade back out at high zoom
        // so the smaller ones underneath become visible
        if (N >= 4) {
          const halfN = Math.ceil(N / 2);
          if (i < halfN) {
            const tc = halfN <= 1 ? 0 : i / (halfN - 1);
            concealMap.set(d.id, LOD_CONCEAL_START + tc * (LOD_CONCEAL_END - LOD_CONCEAL_START));
          } else {
            concealMap.set(d.id, Infinity);
          }
        } else {
          concealMap.set(d.id, Infinity);
        }
      });
    });

    // Build position objects, filtering out regions with no resolvable geo
    const positions = visible.map(d => {
      const geo = getRegionGeo(d);
      if (!geo) return null;
      const px = projection(geo);
      if (!px || !isFinite(px[0])) return null;
      return {
        d,
        x: px[0], y: px[1],
        revealZoom:  revealMap.get(d.id)  ?? LOD_REGION_ALL,
        concealZoom: concealMap.get(d.id) ?? Infinity,
      };
    }).filter(Boolean);

    gRegionBubbles.selectAll('.region-bubble').remove();

    const grps = gRegionBubbles.selectAll('.region-bubble')
      .data(positions, pos => pos.d.id)
      .join('g')
        .attr('class', 'bubble region-bubble')
        .attr('transform', pos => `translate(${pos.x},${pos.y})`)
        .attr('opacity', 0);  // LOD will reveal

    grps.append('circle')
      .attr('r',            pos => getBubbleR(pos.d, currentMetric))
      .attr('fill',         pos => hexToRgba(INDUSTRY_COLORS[pos.d.industry_category], 0.5))
      .attr('stroke',       pos => INDUSTRY_COLORS[pos.d.industry_category])
      .attr('stroke-width', 1.2);
  }

  function refreshBubbles() {
    _rScale = getUnifiedRScale(currentMetric);
    buildCountryBubbles();
    buildRegionBubbles();
    if (!selectedRegion) updateLOD(currentZoom);
    else applyDimming();
    applySearchHighlight();
    updateStats();
  }

  /* ── Visibility filter ──────────────────────────────────── */

  function getVisibleRegions() {
    return allRegions.filter(d => {
      if (!activeIndustries.has(d.industry_category)) return false;
      // In population mode every region with population data is visible regardless of GDP
      const metricVal = currentMetric === 'population' ? d.population : d[currentMetric];
      if (!showUnknownGdp && metricVal === null) return false;
      return true;
    });
  }

  /* ── LOD (Level of Detail) ──────────────────────────────── */

  function updateLOD(k) {
    if (!gCountryBubbles || !gRegionBubbles) return;

    const t = Math.max(0, Math.min(1, (k - LOD_COUNTRY_MAX) / (LOD_REGION_ALL - LOD_COUNTRY_MAX)));

    // Country group: full opacity at low zoom, fades out as regions appear
    gCountryBubbles.attr('opacity', 1 - t);

    // Admin borders: fade in with same range as region bubbles
    // pointer-events follow opacity: on when visible, off when hidden
    if (gAdminBorders) {
      gAdminBorders.attr('opacity', t);
      gAdminBorders.selectAll('.admin-border')
        .attr('pointer-events', t > 0.05 ? 'all' : 'none');
    }

    // Country paths: disable pointer-events when admin borders have taken over
    if (gCountryPaths) {
      gCountryPaths.selectAll('.country-path')
        .attr('pointer-events', t < 0.9 ? 'all' : 'none');
    }

    // Region bubbles: staggered reveal (highest GDP first), then staggered conceal
    // at high zoom so smaller regions underneath become visible
    const FADE = 0.6;
    gRegionBubbles.selectAll('.region-bubble').each(function (pos) {
      const rz = pos.revealZoom;
      const cz = pos.concealZoom;
      let rOp;

      // Reveal phase
      if (k <= rz) {
        rOp = 0;
      } else if (k >= rz + FADE) {
        rOp = 1;
      } else {
        rOp = (k - rz) / FADE;
      }

      // Conceal phase: largest bubbles fade back out at high zoom
      if (isFinite(cz)) {
        if (k >= cz + FADE) {
          rOp = 0;
        } else if (k > cz) {
          rOp = Math.min(rOp, 1 - (k - cz) / FADE);
        }
      }

      d3.select(this).attr('opacity', rOp);
    });
  }

  /* ── Tooltip ────────────────────────────────────────────── */

  /* ── Tooltip helpers ────────────────────────────────────── */

  function showTooltipForDatum(event, d) {
    setEl('tt-region',    d.region);
    setEl('tt-country',   d.country);
    setEl('tt-gdp-total', d.gdp_total      !== null ? fmtGdp(d.gdp_total)    : 'N/A');
    setEl('tt-gdp-pc',    d.gdp_per_capita !== null ? fmtPc(d.gdp_per_capita) : 'N/A');
    setEl('tt-year',      d.gdp_year || (d.isCountryBubble ? 'aggregate' : 'N/A'));
    setEl('tt-industry',  d.industry_category);

    const excerptEl = document.getElementById('tt-excerpt');
    const txt = d.economy_excerpt;
    if (txt) {
      excerptEl.textContent = txt.length > 200 ? txt.slice(0, 200) + '…' : txt;
      excerptEl.style.display = '';
    } else {
      excerptEl.style.display = 'none';
    }

    placeTooltip(event);
    $tooltip.classList.add('visible');
  }

  function onTooltipMove(event)  { placeTooltip(event); }
  function onTooltipLeave()      { $tooltip.classList.remove('visible'); }

  /* ── Country path interaction (national zoom) ───────────── */

  function featureToCountryAggregate(f) {
    const name = ISO_NUM_TO_NAME[String(f.id)];
    if (!name) return null;
    return countryAggregates.find(c => {
      const cn = COUNTRY_ALIASES[c.country] || c.country;
      return cn === name || c.country === name;
    }) || null;
  }

  function onCountryPathEnter(event, f) {
    const agg = featureToCountryAggregate(f);
    if (agg) showTooltipForDatum(event, agg);
  }

  function onCountryPathClick(event, f) {
    event.stopPropagation();
    const agg = featureToCountryAggregate(f);
    if (!agg) return;
    $tooltip.classList.remove('visible');
    if (selectedRegion && selectedRegion.id === agg.id) { closeDetailPanel(); return; }
    selectedRegion    = agg;
    selectedCountryId = agg.id;   // hide its own national bubble
    populatePanel(agg);
    $detailPanel.classList.add('open');
    applyDimming();
  }

  /* ── Admin border interaction (regional zoom) ───────────── */

  // Match a Natural Earth admin-1 feature to a region in allRegions
  function featureToRegion(f) {
    const p = f.properties;
    if (!p) return null;
    const rawAdmin = p.admin || p.geonunit || '';
    const canonical = COUNTRY_ALIASES[rawAdmin] || rawAdmin;
    const names = [p.name, p.name_en, p.name_alt, p.woe_name, p.gn_name].filter(Boolean);

    for (const nm of names) {
      const found = allRegions.find(d => {
        const dc = COUNTRY_ALIASES[d.country] || d.country;
        return dc === canonical && d.region === nm;
      });
      if (found) return found;
    }
    // Case-insensitive fallback
    for (const nm of names) {
      const lc = nm.toLowerCase();
      const found = allRegions.find(d => {
        const dc = COUNTRY_ALIASES[d.country] || d.country;
        return dc === canonical && d.region.toLowerCase() === lc;
      });
      if (found) return found;
    }
    return null;
  }

  function onAdminBorderEnter(event, f) {
    const region = featureToRegion(f);
    if (region) showTooltipForDatum(event, region);
  }

  function onAdminBorderClick(event, f) {
    event.stopPropagation();
    const region = featureToRegion(f);
    if (!region) return;
    $tooltip.classList.remove('visible');
    if (selectedRegion && selectedRegion.id === region.id) { closeDetailPanel(); return; }
    selectedRegion = region;
    // Hide the national bubble for this region's country
    const agg = countryAggregates.find(c => {
      const cn = COUNTRY_ALIASES[c.country] || c.country;
      const rc = COUNTRY_ALIASES[region.country] || region.country;
      return cn === rc || c.country === region.country;
    });
    selectedCountryId = agg ? agg.id : null;
    populatePanel(region);
    $detailPanel.classList.add('open');
    applyDimming();
  }

  function placeTooltip(event) {
    const pad = 16;
    const tw  = $tooltip.offsetWidth  || 260;
    const th  = $tooltip.offsetHeight || 160;
    const vw  = window.innerWidth;
    const vh  = window.innerHeight;
    let x = event.clientX + pad;
    let y = event.clientY + pad;
    if (x + tw > vw - 8) x = event.clientX - tw - pad;
    if (y + th > vh - 8) y = event.clientY - th - pad;
    $tooltip.style.left = x + 'px';
    $tooltip.style.top  = y + 'px';
  }

  /* ── Detail panel ───────────────────────────────────────── */

  function populatePanel(d) {
    setEl('panel-region-name',  d.region);
    setEl('panel-country-name', d.country);

    const statsEl = document.getElementById('panel-stats');
    statsEl.innerHTML = '';
    statsEl.appendChild(makeStatCard('Total GDP',
      d.gdp_total      !== null ? fmtGdp(d.gdp_total)      : 'N/A',
      d.gdp_year       ? 'billion USD ' + d.gdp_year        : 'No data'));
    statsEl.appendChild(makeStatCard('GDP per Capita',
      d.gdp_per_capita !== null ? fmtPc(d.gdp_per_capita)   : 'N/A',
      d.gdp_year       ? 'USD ' + d.gdp_year                : 'No data'));
    if (d.population !== null)
      statsEl.appendChild(makeStatCard('Population', fmtPop(d.population), ''));
    if (d.area_km2 !== null)
      statsEl.appendChild(makeStatCard('Area', fmtArea(d.area_km2), ''));
    if (d.hdi !== null)
      statsEl.appendChild(makeStatCard('HDI', d.hdi.toFixed(3), d.hdi_year ? String(d.hdi_year) : ''));
    if (d.unemployment_rate !== null)
      statsEl.appendChild(makeStatCard('Unemployment', d.unemployment_rate.toFixed(1) + '%', ''));

    // Data quality badge
    const dqBadgeEl = document.getElementById('panel-data-quality');
    if (dqBadgeEl) {
      dqBadgeEl.className = 'dq-badge dq-' + (d.data_quality || 'stub');
      dqBadgeEl.textContent = (d.data_quality || 'stub').toUpperCase();
    }

    const indGdpSec = document.getElementById('panel-industry-gdp-section');
    if (d.industry_gdp && Object.keys(d.industry_gdp).length > 0) {
      const sorted = Object.entries(d.industry_gdp).sort((a, b) => b[1] - a[1]);
      const maxVal = sorted[0][1];
      document.getElementById('panel-industry-gdp-list').innerHTML = sorted.map(([cat, val]) => {
        const pct   = Math.round((val / maxVal) * 100);
        const color = INDUSTRY_COLORS[cat] || '#95a5a6';
        return `<div class="ind-gdp-row">
          <span class="ind-gdp-label" style="color:${color}">${escHtml(cat)}</span>
          <div class="ind-gdp-bar-track">
            <div class="ind-gdp-bar" style="width:${pct}%;background:${color}"></div>
          </div>
          <span class="ind-gdp-val">$${val >= 1 ? val.toFixed(1) + 'B' : (val * 1000).toFixed(0) + 'M'}</span>
        </div>`;
      }).join('');
      indGdpSec.style.display = '';
    } else {
      if (indGdpSec) indGdpSec.style.display = 'none';
    }

    const badgeContainer = document.getElementById('panel-industry-badge');
    badgeContainer.innerHTML = `
      <div class="panel-industry-badge">
        <span class="panel-industry-dot" style="background:${INDUSTRY_COLORS[d.industry_category]}"></span>
        ${escHtml(d.industry_category)}
      </div>`;

    const indSec = document.getElementById('panel-industries-section');
    const indEl  = document.getElementById('panel-industries');
    if (d.primary_industry) {
      indEl.textContent    = d.primary_industry;
      indSec.style.display = '';
    } else {
      indSec.style.display = 'none';
    }

    const excSec = document.getElementById('panel-excerpt-section');
    const excEl  = document.getElementById('panel-excerpt');
    if (d.economy_excerpt) {
      excEl.textContent    = d.economy_excerpt;
      excSec.style.display = '';
    } else {
      excSec.style.display = 'none';
    }

    const wikiSec  = document.getElementById('panel-wiki-section');
    const wikiLink = document.getElementById('panel-wiki-link');
    if (d.wikipedia_url) {
      wikiLink.href        = d.wikipedia_url;
      wikiSec.style.display = '';
    } else {
      wikiSec.style.display = 'none';
    }
  }

  function closeDetailPanel() {
    $detailPanel.classList.remove('open');
    selectedRegion = null;
    applyDimming();
  }

  function applyDimming() {
    if (!gRegionBubbles) return;
    if (selectedRegion) {
      // Hide the national bubble for the selected region's country (or itself if national)
      const hiddenId = selectedCountryId;
      gCountryBubbles.selectAll('.country-bubble')
        .attr('opacity', d => d.id === hiddenId ? 0 : 0.04);
      gRegionBubbles.selectAll('.region-bubble')
        .attr('opacity',    pos => pos.d.id === selectedRegion.id ? 1 : 0.07)
        .classed('highlighted', pos => pos.d.id === selectedRegion.id);
    } else {
      selectedCountryId = null;
      gRegionBubbles.selectAll('.region-bubble').classed('highlighted', false);
      updateLOD(currentZoom);
    }
  }

  function makeStatCard(label, value, sub) {
    const card = document.createElement('div');
    card.className = 'panel-stat-card';
    card.innerHTML = `
      <div class="panel-stat-label">${escHtml(label)}</div>
      <div class="panel-stat-value">${escHtml(value)}</div>
      <div class="panel-stat-sub">${escHtml(sub || '')}</div>`;
    return card;
  }

  /* ── Search ─────────────────────────────────────────────── */

  // Score a region match for search relevance. Industry matches are ranked by
  // importance (exact category > primary_industry keyword), region name matches
  // follow. Within same score bracket, higher GDP = higher rank.
  function scoreSearchResult(d, term) {
    let score = 0;
    // Industry category match (highest priority for industry queries)
    if (d.industry_category.toLowerCase() === term) score += 100;
    else if (d.industry_category.toLowerCase().includes(term)) score += 60;
    // Primary industry keyword match
    if (d.primary_industry) {
      const kwds = d.primary_industry.toLowerCase();
      if (kwds.split(',').map(k => k.trim()).includes(term)) score += 80;
      else if (kwds.includes(term)) score += 40;
    }
    // Region name match
    if (d.region.toLowerCase() === term) score += 90;
    else if (d.region.toLowerCase().startsWith(term)) score += 70;
    else if (d.region.toLowerCase().includes(term)) score += 50;
    // Country name match (lower priority)
    if (d.country.toLowerCase().includes(term)) score += 20;
    // GDP tiebreaker: larger economies rank slightly higher within same score bracket
    if (d.gdp_total) score += Math.min(10, Math.log10(d.gdp_total) * 2);
    return score;
  }

  function onSearchInput() {
    searchTerm = $searchInput.value.trim().toLowerCase();

    if (searchTerm.length < 2) {
      $searchResults.classList.remove('visible');
      $searchResults.innerHTML = '';
      applySearchHighlight();
      return;
    }

    const matches = allRegions
      .map(d => ({ d, score: scoreSearchResult(d, searchTerm) }))
      .filter(({ score }) => score >= 40)
      .sort((a, b) => b.score - a.score)
      .slice(0, 25)
      .map(({ d }) => d);

    renderSearchDropdown(matches);
    applySearchHighlight();
  }

  function renderSearchDropdown(matches) {
    $searchResults.innerHTML = '';
    if (matches.length === 0) {
      const item = document.createElement('div');
      item.className = 'search-result-item';
      item.innerHTML = '<span class="search-result-region" style="color:var(--text-muted)">No results</span>';
      $searchResults.appendChild(item);
    } else {
      matches.forEach(d => {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.innerHTML = `
          <div class="search-result-region">${highlightMatch(d.region, searchTerm)}</div>
          <div class="search-result-country">${escHtml(d.country)}</div>`;
        item.addEventListener('mousedown', e => {
          e.preventDefault();
          $searchInput.value = d.region;
          searchTerm = d.region.toLowerCase();
          $searchResults.classList.remove('visible');
          applySearchHighlight();
          openAndFocusRegion(d);
        });
        $searchResults.appendChild(item);
      });
    }
    $searchResults.classList.add('visible');
  }

  function openAndFocusRegion(d) {
    selectedRegion = d;
    populatePanel(d);
    $detailPanel.classList.add('open');
    applyDimming();

    const geo = getRegionGeo(d);
    if (!geo) return;
    const { w, h } = getMapSize();
    const [px, py] = projection(geo);
    const targetT = d3.zoomIdentity
      .translate(w / 2, h / 2)
      .scale(8)
      .translate(-px, -py);
    svg.transition().duration(650).ease(d3.easeCubicInOut)
      .call(zoomBehaviour.transform, targetT);
  }

  function applySearchHighlight() {
    if (!gRegionBubbles) return;

    if (searchTerm.length < 2) {
      applyDimming();
      gRegionBubbles.selectAll('.region-bubble').classed('search-highlight', false);
      gCountryBubbles.selectAll('.country-bubble').classed('search-highlight', false);
      return;
    }

    gCountryBubbles.attr('opacity', 0.05);

    gRegionBubbles.selectAll('.region-bubble').each(function (pos) {
      const hit = scoreSearchResult(pos.d, searchTerm) >= 40;
      d3.select(this)
        .attr('opacity', hit ? 1 : 0.04)
        .classed('search-highlight', hit);
    });
  }

  /* ── Sidebar UI ─────────────────────────────────────────── */

  function buildSidebarUI() {
    buildIndustryPills();
    renderSizeLegend(currentMetric);
    updateRegionCount();
  }

  function buildCategoryKeywords() {
    // Returns { category: [{keyword, count}, ...] } sorted by count descending, top 10
    const result = {};
    INDUSTRY_ORDER.forEach(cat => { result[cat] = {}; });
    allRegions.forEach(d => {
      if (!d.primary_industry) return;
      const cat = d.industry_category;
      if (!result[cat]) return;
      d.primary_industry.split(',').forEach(kw => {
        const k = kw.trim();
        if (!k) return;
        result[cat][k] = (result[cat][k] || 0) + 1;
      });
    });
    const out = {};
    INDUSTRY_ORDER.forEach(cat => {
      out[cat] = Object.entries(result[cat])
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([keyword, count]) => ({ keyword, count }));
    });
    return out;
  }

  function buildIndustryPills() {
    $industryPillsEl.innerHTML = '';

    // "All" button
    const allBtn = document.createElement('button');
    allBtn.className = 'pill-all-btn';
    allBtn.textContent = 'All';
    allBtn.addEventListener('click', () => {
      INDUSTRY_ORDER.forEach(cat => activeIndustries.add(cat));
      $industryPillsEl.querySelectorAll('.industry-pill').forEach(p => p.classList.remove('inactive'));
      refreshBubbles();
    });
    $industryPillsEl.appendChild(allBtn);

    const catKeywords = buildCategoryKeywords();

    INDUSTRY_ORDER.forEach(cat => {
      const count = allRegions.filter(d => d.industry_category === cat).length;

      // Wrapper holds the pill row + its dropdown
      const wrapper = document.createElement('div');
      wrapper.style.display = 'flex';
      wrapper.style.flexDirection = 'column';

      const pill = document.createElement('div');
      pill.className   = 'industry-pill';
      pill.dataset.cat = cat;
      pill.innerHTML   = `
        <span class="pill-dot" style="background:${INDUSTRY_COLORS[cat]}"></span>
        <span class="pill-label">${escHtml(cat)}</span>
        <span class="pill-count">${count}</span>
        <span class="pill-expand" title="Show top keywords">&#9662;</span>`;

      // Main pill click → toggle (with Ctrl/Cmd = solo)
      pill.addEventListener('click', e => {
        // Ignore if the expand arrow was clicked
        if (e.target.classList.contains('pill-expand')) return;
        toggleIndustry(cat, pill, e);
      });

      // Expand arrow click → toggle dropdown
      const expandBtn = pill.querySelector('.pill-expand');

      const dropdown = document.createElement('div');
      dropdown.className = 'pill-dropdown';

      catKeywords[cat].forEach(({ keyword, count: kwCount }) => {
        const item = document.createElement('div');
        item.className = 'pill-dropdown-item';
        item.innerHTML = `<span class="pill-dropdown-kw">${escHtml(keyword)}</span><span class="pill-dropdown-cnt">${kwCount}</span>`;
        item.addEventListener('click', e => {
          e.stopPropagation();
          $searchInput.value = keyword;
          onSearchInput();
        });
        dropdown.appendChild(item);
      });

      expandBtn.addEventListener('click', e => {
        e.stopPropagation();
        const isOpen = dropdown.classList.toggle('open');
        expandBtn.classList.toggle('open', isOpen);
      });

      wrapper.appendChild(pill);
      wrapper.appendChild(dropdown);
      $industryPillsEl.appendChild(wrapper);
    });
  }

  function toggleIndustry(cat, pill, event) {
    const solo = event && (event.ctrlKey || event.metaKey);
    if (solo) {
      // Ctrl/Cmd+click: isolate this category
      INDUSTRY_ORDER.forEach(c => activeIndustries.delete(c));
      activeIndustries.add(cat);
      $industryPillsEl.querySelectorAll('.industry-pill').forEach(p => {
        p.classList.toggle('inactive', p.dataset.cat !== cat);
      });
    } else {
      if (activeIndustries.has(cat)) {
        if (activeIndustries.size === 1) return;
        activeIndustries.delete(cat);
        pill.classList.add('inactive');
      } else {
        activeIndustries.add(cat);
        pill.classList.remove('inactive');
      }
    }
    refreshBubbles();
  }

  function renderSizeLegend(metric) {
    $sizeLegendEl.innerHTML = '';
    let values, labels;
    if (metric === 'gdp_total') {
      values = LEGEND_GDP_VALUES;
      labels = values.map(v => v >= 1000 ? (v / 1000) + 'T' : v + 'B');
    } else if (metric === 'population') {
      values = LEGEND_POP_VALUES;
      labels = values.map(v => fmtPop(v));
    } else {
      values = LEGEND_PC_VALUES;
      labels = values.map(v => v >= 1000 ? '$' + (v / 1000).toFixed(0) + 'k' : '$' + v);
    }
    const sc = getUnifiedRScale(metric);
    values.forEach((v, i) => {
      const r = sc(v);
      const item = document.createElement('div');
      item.className = 'size-legend-item';
      item.innerHTML = `
        <div class="size-legend-circle" style="width:${r * 2}px;height:${r * 2}px;"></div>
        <div class="size-legend-label">${labels[i]}</div>`;
      $sizeLegendEl.appendChild(item);
    });
  }

  function updateRegionCount() {
    const v = getVisibleRegions().length;
    $regionCountBadge.textContent = `${v.toLocaleString()} / ${allRegions.length.toLocaleString()} regions`;
  }

  function updateStats() {
    const visible = getVisibleRegions();
    $statVisible.textContent = visible.length.toLocaleString();
    if (currentMetric === 'population') {
      const sum = d3.sum(visible, d => d.population || 0);
      $statTotalGdp.textContent = fmtPop(sum);
    } else {
      const sum = d3.sum(visible, d => d.gdp_total || 0);
      $statTotalGdp.textContent = fmtGdpLarge(sum);
    }
    updateRegionCount();
  }

  /* ── Event wiring ───────────────────────────────────────── */

  function wireEvents() {
    document.getElementById('btn-gdp-total').addEventListener('click',  () => setMetric('gdp_total'));
    document.getElementById('btn-gdp-pc').addEventListener('click',     () => setMetric('gdp_per_capita'));
    document.getElementById('btn-population').addEventListener('click', () => setMetric('population'));

    document.getElementById('show-unknown-gdp').addEventListener('change', e => {
      showUnknownGdp = e.target.checked;
      refreshBubbles();
    });

    $searchInput.addEventListener('input', onSearchInput);
    $searchInput.addEventListener('focus', () => {
      if ($searchInput.value.trim().length >= 2) $searchResults.classList.add('visible');
    });
    $searchInput.addEventListener('blur', () => {
      setTimeout(() => $searchResults.classList.remove('visible'), 150);
    });
    document.addEventListener('click', e => {
      if (!e.target.closest('#search-wrapper')) $searchResults.classList.remove('visible');
    });

    document.getElementById('panel-close').addEventListener('click', closeDetailPanel);

    document.getElementById('btn-zoom-in').addEventListener('click', () => {
      svg.transition().duration(280).call(zoomBehaviour.scaleBy, 1.7);
    });
    document.getElementById('btn-zoom-out').addEventListener('click', () => {
      svg.transition().duration(280).call(zoomBehaviour.scaleBy, 1 / 1.7);
    });
    document.getElementById('btn-zoom-reset').addEventListener('click', resetZoom);

    window.addEventListener('resize', debounce(handleResize, 200));
  }

  function setMetric(metric) {
    if (currentMetric === metric) return;
    currentMetric = metric;
    document.getElementById('btn-gdp-total').classList.toggle('active',  metric === 'gdp_total');
    document.getElementById('btn-gdp-pc').classList.toggle('active',     metric === 'gdp_per_capita');
    document.getElementById('btn-population').classList.toggle('active', metric === 'population');
    // Update stats bar label
    const unitEl = document.getElementById('stat-aggregate-unit');
    if (unitEl) unitEl.textContent = metric === 'population' ? 'total population' : 'total GDP';
    renderSizeLegend(metric);
    computeCountryAggregates();
    refreshBubbles();
  }

  function resetZoom() {
    svg.transition().duration(500).ease(d3.easeCubicInOut)
      .call(zoomBehaviour.transform, d3.zoomIdentity);
  }

  function handleResize() {
    const { w, h } = getMapSize();
    projection.translate([w / 2, h / 2]).scale(Math.min(w / 6.28, h / 3.4));
    pathGen = d3.geoPath().projection(projection);
    zoomBehaviour.translateExtent([[-w * 0.6, -h * 0.6], [w * 1.6, h * 1.6]]);
    svg.call(zoomBehaviour.transform, d3.zoomIdentity);
    currentZoom = 1;
    gRoot.selectAll('*').remove();
    drawBaseMap();       // re-creates gAdminBorders
    if (admin1GeoJSON) drawAdminBorders();
    buildCountryBubbles();
    buildRegionBubbles();
    updateLOD(1);
    applySearchHighlight();
  }

  /* ── Formatting helpers ─────────────────────────────────── */

  function fmtPop(v) {
    if (!v) return 'N/A';
    if (v >= 1e9) return (v / 1e9).toFixed(2) + 'B';
    if (v >= 1e6) return (v / 1e6).toFixed(1) + 'M';
    if (v >= 1e3) return (v / 1e3).toFixed(0) + 'K';
    return v.toLocaleString();
  }

  function fmtArea(v) {
    if (!v) return 'N/A';
    return v.toLocaleString(undefined, { maximumFractionDigits: 0 }) + ' km²';
  }

  function fmtGdp(b) {
    if (b === null) return 'N/A';
    if (b >= 1000) return '$' + (b / 1000).toFixed(2) + 'T';
    if (b >= 1)    return '$' + b.toFixed(1) + 'B';
    return '$' + (b * 1000).toFixed(0) + 'M';
  }

  function fmtPc(v) {
    return v === null ? 'N/A' : '$' + Math.round(v).toLocaleString('en-US');
  }

  function fmtGdpLarge(b) {
    if (!b) return '$0';
    if (b >= 1000) return '$' + (b / 1000).toFixed(1) + 'T';
    return '$' + Math.round(b).toLocaleString('en-US') + 'B';
  }

  /* ── Utility ────────────────────────────────────────────── */

  function hexToRgba(hex, alpha) {
    if (!hex || hex.length < 7) return `rgba(149,165,166,${alpha})`;
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
  }

  function escHtml(s) {
    if (!s) return '';
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function highlightMatch(text, term) {
    if (!term) return escHtml(text);
    const safe = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return escHtml(text).replace(
      new RegExp(`(${safe})`, 'gi'),
      '<mark style="background:rgba(88,166,255,0.3);color:inherit;border-radius:2px;padding:0 1px">$1</mark>'
    );
  }

  function setEl(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
  }

  function hideLoading() {
    $loadingOverlay.classList.add('hidden');
    setTimeout(() => { $loadingOverlay.style.display = 'none'; }, 500);
  }

  function showError(msg) {
    $loadingOverlay.style.display = 'none';
    $errorMsg.textContent =
      msg + ' — Run: python3 -m http.server 8000 from the test/ directory, then visit http://localhost:8000/economy-map/';
    $errorOverlay.classList.add('visible');
  }

  /* ── Start ──────────────────────────────────────────────── */

  wireEvents();

  init().then(() => {
    svg.on('click', event => {
      const t = event.target;
      if (
        t === $mapSvg ||
        t.classList.contains('sphere') ||
        t.classList.contains('graticule') ||
        t.tagName === 'svg'
      ) {
        closeDetailPanel();
        if (searchTerm.length < 2) {
          gRegionBubbles  && gRegionBubbles.selectAll('.region-bubble').classed('search-highlight', false);
          gCountryBubbles && gCountryBubbles.selectAll('.country-bubble').classed('search-highlight', false);
        }
      }
    });
  });

})();
