export type Partner={code:number;iso:string|null;name:string;value:number;share:number;quantity:number|null;quantityUnit:string|null;netWeightKg:number|null;quantityEstimated:boolean;netWeightEstimated:boolean}
export type RankCountry={code:number;iso:string|null;name:string;value:number;share:number;rank:number}
export type India8Line={code:string;description:string;imports:number|null;exports:number|null;tradeBalance:number|null;quantity:number|null;quantityUnit:string|null}
export type ChainEdge={hs:string;label:string;relation:string;confidence:string}
export type LiveProduct={
 schemaVersion:string;generatedAt:string;source:string;
 product:{hs6:string;description:string;classification:string;level:number};period:{start:number;end:number;latest:number};
 global:{available:boolean;comparisonYear?:number|null;latestRequestedYear?:number|null;reportedWorldExports:number|null;reportedWorldImports?:number|null;worldExportGrowthYoY:number|null;indiaExportRank:number|null;indiaImportRank?:number|null;indiaExportShare:number|null;indiaImportShare?:number|null;leader:string|null;leaderShare:number|null;reporterCount?:number;coverageStatus?:'validated'|'incomplete'|'unavailable'|'error'|string;coverageNote:string;coverageAudit?:unknown[];topExporters?:RankCountry[];topImporters?:RankCountry[]};
 india:{reporterCode:number;imports:number;exports:number;tradeBalance:number;importGrowthYoY:number|null;exportGrowthYoY:number|null;importCAGR:number|null;exportCAGR:number|null;largestSupplier:Partner|null;largestDestination:Partner|null;supplierConcentration:{largestShare:number|null;top3Share:number|null;hhi:number|null;level:string|null};exportMarketConcentration:{largestShare:number|null;top3Share:number|null;hhi:number|null;level:string|null}};
 trend:Array<{year:number;indiaImports:number|null;indiaExports:number|null;reportedWorldExports:number|null}>;suppliers:Partner[];destinations:Partner[];
 india8:{available:boolean;lines:India8Line[];note:string};
 supplyChain:{available:boolean;upstream:ChainEdge[];downstream:ChainEdge[];context?:string;note:string};
}
export type CatalogueItem={hs6:string;description:string|null;classification:string|null;latest:number|null;globalBenchmarkYear?:number|null;globalCoverageStatus?:string|null;indiaImports:number|null;indiaExports:number|null;indiaExportRank:number|null;indiaExportShare:number|null;largestSupplier?:string|null;largestSupplierShare?:number|null;supplierConcentration?:string|null;exportGrowthYoY?:number|null;generatedAt:string|null;path:string}
export type Catalogue={schemaVersion:string;count:number;products:CatalogueItem[]}
export type HsLibraryItem={code:string;level:number;description:string;parent:string|null;tags:string[];loaded:boolean}
export type HsLibrary={generatedAt:string;items:HsLibraryItem[]}
export async function loadProduct(hs:string):Promise<LiveProduct>{const r=await fetch(`/data/products/${hs}.json`,{cache:'no-store'});if(!r.ok)throw new Error(`HS ${hs} is in the library but its trade snapshot has not been generated.`);return r.json()}
export async function loadCatalogue():Promise<Catalogue>{const r=await fetch('/data/catalogue.json',{cache:'no-store'});return r.ok?r.json():{schemaVersion:'0.4.0',count:0,products:[]}}
export async function loadHsLibrary():Promise<HsLibrary>{const r=await fetch('/data/hs-library.json',{cache:'no-store'});return r.ok?r.json():{generatedAt:'',items:[]}}
