export type Partner = { name: string; value: number; share: number }
export type SeriesPoint = { year: string; world: number; indiaExports: number; indiaImports: number }
export type Product = {
  hs6: string
  name: string
  family: string
  india8: { code: string; name: string; imports: number; exports: number; growth: number }[]
  snapshot: {
    worldTrade: number; worldGrowth: number; leader: string; leaderShare: number;
    indiaRank: number; indiaShare: number; indiaImports: number; indiaExports: number;
    importGrowth: number; exportGrowth: number; supplier: string; supplierShare: number;
    destination: string; destinationShare: number; concentration: 'Low'|'Moderate'|'High';
  }
  trend: SeriesPoint[]
  suppliers: Partner[]
  destinations: Partner[]
  upstream: { hs: string; label: string }[]
  downstream: { hs: string; label: string }[]
}

// DEMONSTRATION DATA ONLY. Values below are synthetic UI fixtures and are not trade statistics.
export const products: Product[] = [
  {
    hs6: '847130',
    name: 'Portable automatic data processing machines',
    family: 'IT Hardware',
    india8: [
      { code: '84713010', name: 'Personal computer (laptop, palmtop etc.)', imports: 4.7, exports: 0.42, growth: 18.4 }
    ],
    snapshot: {
      worldTrade: 148.2, worldGrowth: 4.8, leader: 'China', leaderShare: 62.4,
      indiaRank: 16, indiaShare: 1.7, indiaImports: 5.4, indiaExports: 1.15,
      importGrowth: 8.1, exportGrowth: 31.6, supplier: 'China', supplierShare: 73.2,
      destination: 'United States', destinationShare: 34.5, concentration: 'High'
    },
    trend: [
      { year:'2021', world:121, indiaExports:.28, indiaImports:4.1 },
      { year:'2022', world:128, indiaExports:.39, indiaImports:4.4 },
      { year:'2023', world:133, indiaExports:.57, indiaImports:4.8 },
      { year:'2024', world:141, indiaExports:.84, indiaImports:5.0 },
      { year:'2025', world:148.2, indiaExports:1.15, indiaImports:5.4 }
    ],
    suppliers: [
      { name:'China', value:3.95, share:73.2 }, { name:'Singapore', value:.52, share:9.6 },
      { name:'Vietnam', value:.38, share:7.0 }, { name:'Others', value:.55, share:10.2 }
    ],
    destinations: [
      { name:'United States', value:.40, share:34.5 }, { name:'UAE', value:.18, share:15.7 },
      { name:'Netherlands', value:.13, share:11.2 }, { name:'Others', value:.44, share:38.6 }
    ],
    upstream: [
      { hs:'854231', label:'Processors & controllers' }, { hs:'852411', label:'Flat panel display modules' },
      { hs:'850760', label:'Lithium-ion accumulators' }, { hs:'853400', label:'Printed circuits' }
    ],
    downstream: [
      { hs:'8471xx', label:'Computing systems' }, { hs:'8517xx', label:'Networked equipment' }
    ]
  },
  {
    hs6: '854231', name: 'Electronic integrated circuits: processors and controllers', family: 'Semiconductors',
    india8: [{ code:'85423100', name:'Processors/controllers — India tariff line', imports:8.9, exports:.62, growth:22.7 }],
    snapshot: { worldTrade:212.5, worldGrowth:9.2, leader:'Chinese Taipei', leaderShare:31.4, indiaRank:28, indiaShare:.4, indiaImports:9.6, indiaExports:.74, importGrowth:17.5, exportGrowth:22.9, supplier:'China', supplierShare:35.1, destination:'Singapore', destinationShare:27.8, concentration:'Moderate' },
    trend:[{year:'2021',world:160,indiaExports:.31,indiaImports:6.1},{year:'2022',world:173,indiaExports:.39,indiaImports:6.8},{year:'2023',world:181,indiaExports:.45,indiaImports:7.4},{year:'2024',world:195,indiaExports:.58,indiaImports:8.2},{year:'2025',world:212.5,indiaExports:.74,indiaImports:9.6}],
    suppliers:[{name:'China',value:3.37,share:35.1},{name:'Chinese Taipei',value:2.4,share:25},{name:'South Korea',value:1.34,share:14},{name:'Others',value:2.49,share:25.9}],
    destinations:[{name:'Singapore',value:.21,share:27.8},{name:'Hong Kong',value:.15,share:20.1},{name:'United States',value:.10,share:13.8},{name:'Others',value:.28,share:38.3}],
    upstream:[{hs:'381800',label:'Doped chemical elements / wafers'},{hs:'848620',label:'Semiconductor manufacturing equipment'}],
    downstream:[{hs:'847130',label:'Portable computers'},{hs:'851713',label:'Smartphones'},{hs:'8528xx',label:'Displays / monitors'}]
  },
  {
    hs6:'850760', name:'Lithium-ion accumulators', family:'Batteries & Energy Storage',
    india8:[{code:'85076000',name:'Lithium-ion accumulators — India tariff line',imports:4.1,exports:.46,growth:29.3}],
    snapshot:{worldTrade:96.8,worldGrowth:14.6,leader:'China',leaderShare:55.8,indiaRank:18,indiaShare:.8,indiaImports:4.4,indiaExports:.61,importGrowth:24.2,exportGrowth:28.7,supplier:'China',supplierShare:71.4,destination:'United States',destinationShare:29.1,concentration:'High'},
    trend:[{year:'2021',world:49,indiaExports:.16,indiaImports:1.9},{year:'2022',world:59,indiaExports:.21,indiaImports:2.4},{year:'2023',world:70,indiaExports:.31,indiaImports:3.0},{year:'2024',world:84,indiaExports:.44,indiaImports:3.7},{year:'2025',world:96.8,indiaExports:.61,indiaImports:4.4}],
    suppliers:[{name:'China',value:3.14,share:71.4},{name:'South Korea',value:.42,share:9.5},{name:'Japan',value:.31,share:7.0},{name:'Others',value:.53,share:12.1}],
    destinations:[{name:'United States',value:.18,share:29.1},{name:'Germany',value:.10,share:16.4},{name:'UAE',value:.08,share:13.1},{name:'Others',value:.25,share:41.4}],
    upstream:[{hs:'282520',label:'Lithium oxide/hydroxide'},{hs:'283691',label:'Lithium carbonates'},{hs:'7505xx',label:'Nickel inputs'}],
    downstream:[{hs:'847130',label:'Portable computers'},{hs:'851713',label:'Smartphones'},{hs:'8703xx',label:'Electric vehicles'}]
  }
]

export const overview = {
  worldTrade: 2.94,
  worldGrowth: 6.8,
  indiaExportRank: 11,
  indiaShare: 3.1,
  indiaExports: 38.6,
  indiaImports: 89.2,
  balance: -50.6
}
