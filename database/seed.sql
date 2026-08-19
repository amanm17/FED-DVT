INSERT OR IGNORE INTO products (hs6,name,family,hs_version,strategic_relevance) VALUES
('847130','Portable automatic data processing machines','IT Hardware','HS2022','high'),
('854231','Electronic integrated circuits: processors and controllers','Semiconductors','HS2022','high'),
('850760','Lithium-ion accumulators','Batteries & Energy Storage','HS2022','high');
INSERT OR IGNORE INTO india_tariff_lines (code,parent_hs6,name,itchs_version,source) VALUES
('84713010','847130','Personal computer (laptop, palmtop etc.)','ITC(HS)','DGFT'),
('85423100','854231','India tariff line under HS 854231','ITC(HS)','DGFT'),
('85076000','850760','India tariff line under HS 850760','ITC(HS)','DGFT');
