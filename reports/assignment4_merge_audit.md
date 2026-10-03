# Assignment 4.12 Merge Audit

## Scope

Primary panel: metropolitan MSA x 2022 NAICS sector x year; 2010-2023. BDS micropolitan intermediate rows excluded: 89,820. Metropolitan codes in BDS: 387.

Industry codes are official standardized 2022 broad sectors. Unresolved source sectors: none.

## Source Key Checks

| Source | Rows | Duplicate keys |
| --- | ---: | ---: |
| BDS | 178,382 | 0 |
| QCEW | 179,731 | 0 |
| ACS | 5,194 | 0 |
| CBP | 189,474 | 0 |

## Common Industries

| Source | Sectors |
| --- | --- |
| BDS | 11, 21, 22, 23, 31-33, 42, 44-45, 48-49, 51, 52, 53, 54, 55, 56, 61, 62, 71, 72, 81 |
| QCEW | 11, 21, 22, 23, 31-33, 42, 44-45, 48-49, 51, 52, 53, 54, 55, 56, 61, 62, 71, 72, 81 |
| CBP | 11, 21, 22, 23, 31-33, 42, 44-45, 48-49, 51, 52, 53, 54, 55, 56, 61, 62, 71, 72, 81 |

Common sectors: 11, 21, 22, 23, 31-33, 42, 44-45, 48-49, 51, 52, 53, 54, 55, 56, 61, 62, 71, 72, 81.
Sectors missing from one or more sources: none.

## Merge Audits

| Merge | Before rows | Matched | Left-only | Right-only | After rows | Match rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BDS inner QCEW | BDS 88,562; QCEW 71,800 | 63,577 | BDS 24,985 | QCEW 8,223 | 63,577 | 71.79% of BDS; 88.55% of QCEW |
| + ACS left | 63,577 | 60,039 | 3,538 | 0 | 63,577 | 94.44% |
| + CBP left | 63,577 | 58,236 | 5,341 | 0 | 63,577 | 91.60% |

The core uses an inner BDS-QCEW join because both accepted BDS startup and QCEW growth observations define the primary research relationship. ACS and CBP are left-joined so missing controls/support measures do not remove core observations. ACS and source key uniqueness are checked before integration.

## Final Panel

Rows: 63,577; MSAs: 381; industries: 19; years: 2010-2023; MSA-industry panels: 5,887; 14-year balanced panels: 2,830; unbalanced panels: 3,057; average rows/panel: 10.80; duplicate keys: 0.


### Source Quality Flags

| Flag | Rows flagged |
| --- | ---: |
| `bds_has_suppression` | 0 |
| `bds_startup_available` | 63,577 |
| `qcew_has_suppression` | 0 |
| `acs_matched` | 60,039 |
| `acs_has_suppression` | 0 |
| `acs_has_missing_controls` | 3,538 |
| `cbp_matched` | 58,236 |
| `cbp_has_suppression` | 4,877 |
| `has_suppression` | 4,877 |
| `qcew_incomplete_county_coverage` | 0 |
| `cbp_incomplete_county_coverage` | 5,331 |

### Year Coverage

| Year | Rows | MSAs | Sectors | Startup rate | QCEW growth | ACS complete | CBP matched |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2010 | 4,509 | 379 | 19 | 4,509 | 0 | 4,016 | 3,661 |
| 2011 | 4,515 | 380 | 19 | 4,515 | 4,389 | 4,011 | 3,590 |
| 2012 | 4,487 | 381 | 19 | 4,487 | 4,338 | 3,989 | 3,572 |
| 2013 | 4,512 | 381 | 19 | 4,512 | 4,353 | 4,300 | 3,590 |
| 2014 | 4,551 | 381 | 19 | 4,551 | 4,399 | 4,328 | 3,631 |
| 2015 | 4,534 | 380 | 19 | 4,534 | 4,398 | 4,294 | 4,388 |
| 2016 | 4,522 | 380 | 19 | 4,522 | 4,401 | 4,302 | 4,394 |
| 2017 | 4,522 | 379 | 19 | 4,522 | 4,364 | 4,302 | 4,384 |
| 2018 | 4,539 | 380 | 19 | 4,539 | 4,400 | 4,329 | 4,479 |
| 2019 | 4,540 | 380 | 19 | 4,540 | 4,395 | 4,360 | 4,477 |
| 2020 | 4,523 | 380 | 19 | 4,523 | 4,370 | 4,348 | 4,456 |
| 2021 | 4,544 | 381 | 19 | 4,544 | 4,384 | 4,364 | 4,470 |
| 2022 | 4,662 | 380 | 19 | 4,662 | 4,454 | 4,479 | 4,592 |
| 2023 | 4,617 | 381 | 19 | 4,617 | 4,464 | 4,617 | 4,552 |

QCEW 2010 levels are present, but 2010 growth fields lack a prior-year observation within the source window. 2010 remains in the panel rather than being silently removed.

### Sector Coverage

| Sector | Rows | MSAs | Years | Startup | QCEW growth | ACS complete | CBP matched |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 11 | 1,206 | 214 | 14 | 1,206 | 1,032 | 1,127 | 845 |
| 21 | 1,443 | 186 | 14 | 1,443 | 1,279 | 1,358 | 1,123 |
| 22 | 1,690 | 199 | 14 | 1,690 | 1,513 | 1,607 | 1,150 |
| 23 | 4,818 | 367 | 14 | 4,818 | 4,404 | 4,562 | 4,614 |
| 31-33 | 4,310 | 366 | 14 | 4,310 | 3,947 | 4,103 | 3,882 |
| 42 | 3,053 | 317 | 14 | 3,053 | 2,688 | 2,895 | 2,824 |
| 44-45 | 5,213 | 381 | 14 | 5,213 | 4,816 | 4,923 | 5,135 |
| 48-49 | 2,916 | 286 | 14 | 2,916 | 2,575 | 2,767 | 2,750 |
| 51 | 2,891 | 337 | 14 | 2,891 | 2,585 | 2,720 | 2,468 |
| 52 | 4,154 | 365 | 14 | 4,154 | 3,769 | 3,951 | 3,854 |
| 53 | 4,362 | 350 | 14 | 4,362 | 3,950 | 4,122 | 3,818 |
| 54 | 3,643 | 345 | 14 | 3,643 | 3,150 | 3,431 | 3,447 |
| 55 | 2,006 | 225 | 14 | 2,006 | 1,796 | 1,884 | 1,628 |
| 56 | 3,762 | 343 | 14 | 3,762 | 3,307 | 3,552 | 3,503 |
| 61 | 2,322 | 252 | 14 | 2,322 | 2,096 | 2,185 | 2,072 |
| 62 | 3,448 | 306 | 14 | 3,448 | 3,077 | 3,213 | 3,359 |
| 71 | 3,398 | 326 | 14 | 3,398 | 3,093 | 3,204 | 3,007 |
| 72 | 4,273 | 346 | 14 | 4,273 | 3,865 | 4,018 | 4,217 |
| 81 | 4,669 | 376 | 14 | 4,669 | 4,167 | 4,417 | 4,540 |

### MSA Coverage

Every MSA's row, industry, and year counts are listed; the lowest-coverage MSAs are shown first.

| CBSA | Name | Rows | Sectors | Years |
| --- | --- | ---: | ---: | ---: |
| 46660 | Valdosta, GA | 8 | 2 | 7 |
| 17980 | Columbus, GA-AL | 13 | 1 | 13 |
| 17140 | Cincinnati, OH-KY-IN | 17 | 3 | 14 |
| 40060 | Richmond, VA | 20 | 3 | 12 |
| 31420 | Macon-Bibb County, GA | 21 | 4 | 14 |
| 11100 | Amarillo, TX | 22 | 6 | 14 |
| 47260 | Virginia Beach-Chesapeake-Norfolk, VA-NC | 25 | 4 | 14 |
| 31180 | Lubbock, TX | 26 | 4 | 14 |
| 32820 | Memphis, TN-MS-AR | 35 | 5 | 14 |
| 12940 | Baton Rouge, LA | 41 | 6 | 14 |
| 41180 | St. Louis, MO-IL | 42 | 5 | 14 |
| 47900 | Washington-Arlington-Alexandria, DC-VA-MD-WV | 42 | 7 | 14 |
| 37140 | Paducah, KY-IL | 44 | 9 | 14 |
| 13900 | Bismarck, ND | 46 | 11 | 14 |
| 14540 | Bowling Green, KY | 48 | 6 | 14 |
| 25980 | Hinesville, GA | 50 | 8 | 13 |
| 21340 | El Paso, TX | 53 | 8 | 14 |
| 40220 | Roanoke, VA | 54 | 7 | 14 |
| 31140 | Louisville/Jefferson County, KY-IN | 56 | 10 | 14 |
| 45820 | Topeka, KS | 56 | 7 | 14 |
| 28140 | Kansas City, MO-KS | 58 | 8 | 14 |
| 28940 | Knoxville, TN | 58 | 11 | 14 |
| 33500 | Minot, ND | 58 | 10 | 14 |
| 34980 | Nashville-Davidson--Murfreesboro--Franklin, TN | 58 | 7 | 14 |
| 16020 | Cape Girardeau, MO-IL | 59 | 8 | 14 |
| 29200 | Lafayette-West Lafayette, IN | 59 | 9 | 14 |
| 12060 | Atlanta-Sandy Springs-Roswell, GA | 65 | 6 | 14 |
| 16860 | Chattanooga, TN-GA | 65 | 10 | 14 |
| 16620 | Charleston, WV | 67 | 11 | 14 |
| 37620 | Parkersburg-Vienna, WV | 68 | 10 | 14 |
| 46220 | Tuscaloosa, AL | 68 | 8 | 14 |
| 27620 | Jefferson City, MO | 69 | 10 | 14 |
| 13980 | Blacksburg-Christiansburg-Radford, VA | 73 | 9 | 14 |
| 24260 | Grand Island, NE | 74 | 8 | 14 |
| 26580 | Huntington-Ashland, WV-KY-OH | 74 | 10 | 14 |
| 41660 | San Angelo, TX | 75 | 10 | 14 |
| 49020 | Winchester, VA-WV | 75 | 9 | 14 |
| 37900 | Peoria, IL | 77 | 11 | 14 |
| 43620 | Sioux Falls, SD-MN | 78 | 9 | 14 |
| 12260 | Augusta-Richmond County, GA-SC | 80 | 8 | 14 |
| 27180 | Jackson, TN | 80 | 9 | 14 |
| 28700 | Kingsport-Bristol, TN-VA | 81 | 12 | 14 |
| 36980 | Owensboro, KY | 81 | 11 | 14 |
| 14260 | Boise City, ID | 82 | 12 | 14 |
| 17900 | Columbia, SC | 83 | 11 | 14 |
| 48260 | Weirton-Steubenville, WV-OH | 83 | 13 | 14 |
| 46140 | Tulsa, OK | 84 | 13 | 14 |
| 19740 | Denver-Aurora-Centennial, CO | 86 | 13 | 14 |
| 41140 | St. Joseph, MO-KS | 86 | 10 | 14 |
| 26820 | Idaho Falls, ID | 87 | 14 | 14 |
| 30780 | Little Rock-North Little Rock-Conway, AR | 87 | 9 | 14 |
| 20020 | Dothan, AL | 89 | 12 | 14 |
| 17860 | Columbia, MO | 91 | 11 | 14 |
| 30020 | Lawton, OK | 91 | 11 | 14 |
| 33860 | Montgomery, AL | 91 | 14 | 14 |
| 45460 | Terre Haute, IN | 91 | 11 | 14 |
| 10780 | Alexandria, LA | 92 | 12 | 14 |
| 12020 | Athens-Clarke County, GA | 93 | 9 | 14 |
| 12220 | Auburn-Opelika, AL | 94 | 12 | 14 |
| 48660 | Wichita Falls, TX | 94 | 10 | 14 |
| 13820 | Birmingham, AL | 95 | 13 | 14 |
| 16980 | Chicago-Naperville-Elgin, IL-IN | 95 | 11 | 14 |
| 45500 | Texarkana, TX-AR | 95 | 9 | 14 |
| 15260 | Brunswick-St. Simons, GA | 96 | 10 | 14 |
| 17300 | Clarksville, TN-KY | 97 | 10 | 14 |
| 47020 | Victoria, TX | 97 | 16 | 14 |
| 27140 | Jackson, MS | 99 | 11 | 14 |
| 10500 | Albany, GA | 100 | 12 | 14 |
| 16740 | Charlotte-Concord-Gastonia, NC-SC | 101 | 11 | 14 |
| 26900 | Indianapolis-Carmel-Greenwood, IN | 101 | 13 | 14 |
| 47380 | Waco, TX | 106 | 11 | 14 |
| 44180 | Springfield, MO | 107 | 10 | 14 |
| 17420 | Cleveland, TN | 110 | 12 | 14 |
| 24580 | Green Bay, WI | 110 | 11 | 14 |
| 25620 | Hattiesburg, MS | 110 | 16 | 14 |
| 25740 | Helena, MT | 110 | 15 | 14 |
| 29340 | Lake Charles, LA | 112 | 13 | 14 |
| 30300 | Lewiston, ID-WA | 112 | 13 | 14 |
| 33540 | Missoula, MT | 112 | 14 | 14 |
| 47940 | Waterloo-Cedar Falls, IA | 112 | 13 | 14 |
| 34100 | Morristown, TN | 113 | 12 | 14 |
| 31340 | Lynchburg, VA | 114 | 11 | 14 |
| 37460 | Panama City-Panama City Beach, FL | 114 | 14 | 14 |
| 33260 | Midland, TX | 115 | 13 | 14 |
| 36540 | Omaha, NE-IA | 115 | 12 | 14 |
| 48540 | Wheeling, WV-OH | 116 | 14 | 14 |
| 27740 | Johnson City, TN | 117 | 11 | 14 |
| 39900 | Reno, NV | 117 | 14 | 14 |
| 19140 | Dalton, GA | 118 | 12 | 14 |
| 33740 | Monroe, LA | 119 | 13 | 14 |
| 31740 | Manhattan, KS | 121 | 13 | 14 |
| 35380 | New Orleans-Metairie, LA | 121 | 10 | 14 |
| 20580 | Eagle Pass, TX | 122 | 15 | 14 |
| 10740 | Albuquerque, NM | 123 | 16 | 14 |
| 26420 | Houston-Pasadena-The Woodlands, TX | 123 | 16 | 14 |
| 23540 | Gainesville, FL | 126 | 13 | 14 |
| 31860 | Mankato, MN | 126 | 13 | 14 |
| 29100 | La Crosse-Onalaska, WI-MN | 127 | 15 | 14 |
| 39340 | Provo-Orem-Lehi, UT | 127 | 14 | 14 |
| 42340 | Savannah, GA | 127 | 14 | 14 |
| 15540 | Burlington-South Burlington, VT | 128 | 14 | 14 |
| 16820 | Charlottesville, VA | 128 | 12 | 14 |
| 19460 | Decatur, AL | 129 | 15 | 14 |
| 33460 | Minneapolis-St. Paul-Bloomington, MN-WI | 129 | 12 | 14 |
| 21060 | Elizabethtown, KY | 130 | 12 | 14 |
| 36420 | Oklahoma City, OK | 132 | 16 | 14 |
| 44420 | Staunton-Stuarts Draft, VA | 132 | 14 | 14 |
| 22220 | Fayetteville-Springdale-Rogers, AR | 133 | 12 | 14 |
| 18140 | Columbus, OH | 134 | 11 | 14 |
| 30460 | Lexington-Fayette, KY | 135 | 12 | 14 |
| 38900 | Portland-Vancouver-Hillsboro, OR-WA | 135 | 13 | 14 |
| 16580 | Champaign-Urbana, IL | 136 | 14 | 14 |
| 40340 | Rochester, MN | 136 | 13 | 14 |
| 45220 | Tallahassee, FL | 136 | 14 | 14 |
| 11180 | Ames, IA | 137 | 16 | 14 |
| 14020 | Bloomington, IN | 137 | 16 | 14 |
| 11540 | Appleton, WI | 140 | 16 | 14 |
| 16300 | Cedar Rapids, IA | 140 | 14 | 14 |
| 19780 | Des Moines-West Des Moines, IA | 140 | 13 | 14 |
| 23060 | Fort Wayne, IN | 140 | 13 | 14 |
| 41540 | Salisbury, MD | 140 | 14 | 14 |
| 49180 | Winston-Salem, NC | 141 | 15 | 14 |
| 28660 | Killeen-Temple, TX | 142 | 14 | 14 |
| 30500 | Lexington Park, MD | 142 | 16 | 14 |
| 40580 | Rocky Mount, NC | 142 | 14 | 14 |
| 43580 | Sioux City, IA-NE-SD | 142 | 12 | 14 |
| 11700 | Asheville, NC | 143 | 12 | 14 |
| 44100 | Springfield, IL | 143 | 13 | 14 |
| 45900 | Traverse City, MI | 143 | 13 | 14 |
| 24340 | Grand Rapids-Wyoming-Kentwood, MI | 144 | 13 | 14 |
| 27900 | Joplin, MO-KS | 144 | 13 | 14 |
| 25180 | Hagerstown-Martinsburg, MD-WV | 145 | 15 | 14 |
| 31540 | Madison, WI | 145 | 12 | 14 |
| 41780 | Sandusky, OH | 145 | 14 | 14 |
| 41700 | San Antonio-New Braunfels, TX | 147 | 14 | 14 |
| 48620 | Wichita, KS | 147 | 13 | 14 |
| 25060 | Gulfport-Biloxi, MS | 151 | 14 | 14 |
| 27860 | Jonesboro, AR | 151 | 16 | 14 |
| 21780 | Evansville, IN | 152 | 17 | 14 |
| 25860 | Hickory-Lenoir-Morganton, NC | 152 | 17 | 14 |
| 33780 | Monroe, MI | 156 | 15 | 14 |
| 43900 | Spartanburg, SC | 157 | 16 | 14 |
| 47460 | Walla Walla, WA | 157 | 16 | 14 |
| 12980 | Battle Creek, MI | 158 | 17 | 14 |
| 33220 | Midland, MI | 158 | 16 | 14 |
| 34060 | Morgantown, WV | 158 | 18 | 14 |
| 19340 | Davenport-Moline-Rock Island, IA-IL | 159 | 13 | 14 |
| 39660 | Rapid City, SD | 159 | 15 | 14 |
| 27260 | Jacksonville, FL | 160 | 14 | 14 |
| 46300 | Twin Falls, ID | 161 | 16 | 14 |
| 47580 | Warner Robins, GA | 161 | 16 | 14 |
| 21300 | Elmira, NY | 162 | 17 | 14 |
| 45780 | Toledo, OH | 162 | 15 | 14 |
| 13740 | Billings, MT | 163 | 17 | 14 |
| 10180 | Abilene, TX | 164 | 17 | 14 |
| 40380 | Rochester, NY | 164 | 15 | 14 |
| 40660 | Rome, GA | 164 | 17 | 14 |
| 28100 | Kankakee, IL | 165 | 17 | 14 |
| 17780 | College Station-Bryan, TX | 166 | 16 | 14 |
| 38240 | Pinehurst-Southern Pines, NC | 166 | 19 | 14 |
| 24020 | Glens Falls, NY | 167 | 17 | 14 |
| 30700 | Lincoln, NE | 168 | 14 | 14 |
| 18580 | Corpus Christi, TX | 169 | 16 | 14 |
| 49700 | Yuba City, CA | 169 | 17 | 14 |
| 13020 | Bay City, MI | 170 | 17 | 14 |
| 24860 | Greenville-Anderson-Greer, SC | 170 | 15 | 14 |
| 33140 | Michigan City-La Porte, IN | 170 | 18 | 14 |
| 21420 | Enid, OK | 171 | 19 | 14 |
| 25500 | Harrisonburg, VA | 171 | 16 | 14 |
| 34740 | Muskegon-Norton Shores, MI | 171 | 17 | 14 |
| 30860 | Logan, UT-ID | 172 | 17 | 14 |
| 19500 | Decatur, IL | 174 | 19 | 14 |
| 29020 | Kokomo, IN | 174 | 17 | 14 |
| 48900 | Wilmington, NC | 174 | 14 | 14 |
| 13780 | Binghamton, NY | 175 | 18 | 14 |
| 23900 | Gettysburg, PA | 175 | 19 | 14 |
| 24140 | Goldsboro, NC | 175 | 17 | 14 |
| 34620 | Muncie, IN | 175 | 18 | 14 |
| 43100 | Sheboygan, WI | 175 | 17 | 14 |
| 22180 | Fayetteville, NC | 176 | 15 | 14 |
| 24220 | Grand Forks, ND-MN | 176 | 17 | 14 |
| 22900 | Fort Smith, AR-OK | 177 | 17 | 14 |
| 43780 | South Bend-Mishawaka, IN-MI | 177 | 16 | 14 |
| 30620 | Lima, OH | 178 | 18 | 14 |
| 35620 | New York-Newark-Jersey City, NY-NJ | 178 | 14 | 14 |
| 36260 | Ogden, UT | 178 | 17 | 14 |
| 38540 | Pocatello, ID | 178 | 17 | 14 |
| 16180 | Carson City, NV | 179 | 15 | 14 |
| 18700 | Corvallis, OR | 179 | 18 | 14 |
| 27060 | Ithaca, NY | 179 | 16 | 14 |
| 37980 | Philadelphia-Camden-Wilmington, PA-NJ-DE-MD | 179 | 17 | 14 |
| 18020 | Columbus, IN | 180 | 18 | 14 |
| 30140 | Lebanon, PA | 180 | 18 | 14 |
| 30980 | Longview, TX | 180 | 18 | 14 |
| 24420 | Grants Pass, OR | 181 | 17 | 14 |
| 13460 | Bend, OR | 182 | 16 | 14 |
| 31900 | Mansfield, OH | 182 | 18 | 14 |
| 39300 | Providence-Warwick, RI-MA | 182 | 16 | 14 |
| 20260 | Duluth, MN-WI | 183 | 15 | 14 |
| 44220 | Springfield, OH | 183 | 17 | 14 |
| 47220 | Vineland, NJ | 183 | 19 | 14 |
| 20740 | Eau Claire, WI | 184 | 17 | 14 |
| 41060 | St. Cloud, MN | 184 | 17 | 14 |
| 41940 | San Jose-Sunnyvale-Santa Clara, CA | 184 | 16 | 14 |
| 22540 | Fond du Lac, WI | 185 | 17 | 14 |
| 48300 | Wenatchee-East Wenatchee, WA | 185 | 17 | 14 |
| 19430 | Dayton-Kettering-Beavercreek, OH | 186 | 16 | 14 |
| 25260 | Hanford-Corcoran, CA | 186 | 17 | 14 |
| 25420 | Harrisburg-Carlisle, PA | 186 | 15 | 14 |
| 26980 | Iowa City, IA | 186 | 15 | 14 |
| 38860 | Portland-South Portland, ME | 186 | 14 | 14 |
| 44940 | Sumter, SC | 187 | 18 | 14 |
| 13220 | Beckley, WV | 188 | 19 | 14 |
| 27100 | Jackson, MI | 188 | 17 | 14 |
| 28420 | Kennewick-Richland, WA | 188 | 14 | 14 |
| 36780 | Oshkosh-Neenah, WI | 188 | 15 | 14 |
| 22520 | Florence-Muscle Shoals, AL | 189 | 17 | 14 |
| 28450 | Kenosha, WI | 189 | 17 | 14 |
| 45060 | Syracuse, NY | 189 | 17 | 14 |
| 10580 | Albany-Schenectady-Troy, NY | 190 | 15 | 14 |
| 11500 | Anniston-Oxford, AL | 190 | 17 | 14 |
| 23460 | Gadsden, AL | 190 | 19 | 14 |
| 29620 | Lansing-East Lansing, MI | 190 | 16 | 14 |
| 32900 | Merced, CA | 190 | 17 | 14 |
| 40980 | Saginaw, MI | 190 | 18 | 14 |
| 35660 | Niles, MI | 191 | 17 | 14 |
| 48680 | Wildwood-The Villages, FL | 191 | 19 | 14 |
| 10900 | Allentown-Bethlehem-Easton, PA-NJ | 192 | 17 | 14 |
| 14010 | Bloomington, IL | 192 | 18 | 14 |
| 40420 | Rockford, IL | 192 | 15 | 14 |
| 11020 | Altoona, PA | 193 | 19 | 14 |
| 12580 | Baltimore-Columbia-Towson, MD | 193 | 16 | 14 |
| 22020 | Fargo, ND-MN | 193 | 17 | 14 |
| 39580 | Raleigh-Cary, NC | 193 | 17 | 14 |
| 44060 | Spokane-Spokane Valley, WA | 193 | 16 | 14 |
| 48140 | Wausau, WI | 193 | 17 | 14 |
| 15940 | Canton-Massillon, OH | 195 | 17 | 14 |
| 42540 | Scranton--Wilkes-Barre, PA | 195 | 19 | 14 |
| 27500 | Janesville-Beloit, WI | 196 | 19 | 14 |
| 30340 | Lewiston-Auburn, ME | 197 | 18 | 14 |
| 20100 | Dover, DE | 198 | 17 | 14 |
| 25940 | Hilton Head Island-Bluffton-Port Royal, SC | 198 | 18 | 14 |
| 39540 | Racine-Mount Pleasant, WI | 198 | 17 | 14 |
| 19820 | Detroit-Warren-Dearborn, MI | 199 | 18 | 14 |
| 20220 | Dubuque, IA | 199 | 17 | 14 |
| 42700 | Sebring, FL | 199 | 18 | 14 |
| 48700 | Williamsport, PA | 199 | 19 | 14 |
| 21140 | Elkhart-Goshen, IN | 201 | 19 | 14 |
| 21820 | Fairbanks-College, AK | 201 | 19 | 14 |
| 22500 | Florence, SC | 201 | 18 | 14 |
| 27340 | Jacksonville, NC | 201 | 17 | 14 |
| 27780 | Johnstown, PA | 201 | 19 | 14 |
| 14460 | Boston-Cambridge-Newton, MA-NH | 202 | 15 | 14 |
| 33340 | Milwaukee-Waukesha, WI | 202 | 15 | 14 |
| 26620 | Huntsville, AL | 203 | 16 | 14 |
| 20500 | Durham-Chapel Hill, NC | 204 | 17 | 14 |
| 38940 | Port St. Lucie, FL | 204 | 18 | 14 |
| 31020 | Longview-Kelso, WA | 205 | 19 | 14 |
| 16700 | Charleston-North Charleston, SC | 206 | 18 | 14 |
| 19100 | Dallas-Fort Worth-Arlington, TX | 206 | 17 | 14 |
| 19660 | Deltona-Daytona Beach-Ormond Beach, FL | 206 | 18 | 14 |
| 29940 | Lawrence, KS | 206 | 18 | 14 |
| 10540 | Albany, OR | 207 | 19 | 14 |
| 17410 | Cleveland, OH | 207 | 17 | 14 |
| 43340 | Shreveport-Bossier City, LA | 207 | 17 | 14 |
| 43420 | Sierra Vista-Douglas, AZ | 207 | 19 | 14 |
| 41420 | Salem, OR | 208 | 17 | 14 |
| 15500 | Burlington, NC | 209 | 18 | 14 |
| 41620 | Salt Lake City-Murray, UT | 210 | 19 | 14 |
| 41860 | San Francisco-Oakland-Fremont, CA | 210 | 18 | 14 |
| 48060 | Watertown-Fort Drum, NY | 210 | 19 | 14 |
| 22140 | Farmington, NM | 211 | 19 | 14 |
| 24660 | Greensboro-High Point, NC | 211 | 17 | 14 |
| 24780 | Greenville, NC | 211 | 19 | 14 |
| 12620 | Bangor, ME | 212 | 18 | 14 |
| 20940 | El Centro, CA | 213 | 19 | 14 |
| 26300 | Hot Springs, AR | 213 | 19 | 14 |
| 24500 | Great Falls, MT | 214 | 19 | 14 |
| 28020 | Kalamazoo-Portage, MI | 214 | 17 | 14 |
| 40900 | Sacramento-Roseville-Folsom, CA | 214 | 19 | 14 |
| 22420 | Flint, MI | 215 | 19 | 14 |
| 29180 | Lafayette, LA | 215 | 19 | 14 |
| 39380 | Pueblo, CO | 215 | 19 | 14 |
| 12100 | Atlantic City-Hammonton, NJ | 216 | 19 | 14 |
| 10420 | Akron, OH | 217 | 19 | 14 |
| 16540 | Chambersburg, PA | 217 | 19 | 14 |
| 29420 | Lake Havasu City-Kingman, AZ | 217 | 18 | 14 |
| 38340 | Pittsfield, MA | 218 | 19 | 14 |
| 42680 | Sebastian-Vero Beach-West Vero Corridor, FL | 218 | 19 | 14 |
| 43300 | Sherman-Denison, TX | 218 | 19 | 14 |
| 34900 | Napa, CA | 219 | 18 | 14 |
| 44300 | State College, PA | 219 | 19 | 14 |
| 49740 | Yuma, AZ | 220 | 19 | 14 |
| 13140 | Beaumont-Port Arthur, TX | 221 | 19 | 14 |
| 17820 | Colorado Springs, CO | 221 | 18 | 14 |
| 25220 | Hammond, LA | 221 | 19 | 14 |
| 26140 | Homosassa Springs, FL | 221 | 19 | 14 |
| 28880 | Kiryas Joel-Poughkeepsie-Newburgh, NY | 221 | 18 | 14 |
| 42100 | Santa Cruz-Watsonville, CA | 221 | 19 | 14 |
| 12700 | Barnstable Town, MA | 222 | 19 | 14 |
| 28740 | Kingston, NY | 222 | 19 | 14 |
| 36220 | Odessa, TX | 222 | 18 | 14 |
| 29740 | Las Cruces, NM | 223 | 19 | 14 |
| 39820 | Redding, CA | 223 | 19 | 14 |
| 33700 | Modesto, CA | 224 | 19 | 14 |
| 34580 | Mount Vernon-Anacortes, WA | 224 | 19 | 14 |
| 22380 | Flagstaff, AZ | 225 | 19 | 14 |
| 39460 | Punta Gorda, FL | 225 | 19 | 14 |
| 23580 | Gainesville, GA | 226 | 19 | 14 |
| 12420 | Austin-Round Rock-San Marcos, TX | 227 | 19 | 14 |
| 15380 | Buffalo-Cheektowaga, NY | 227 | 17 | 14 |
| 21500 | Erie, PA | 227 | 19 | 14 |
| 44140 | Springfield, MA | 227 | 19 | 14 |
| 23420 | Fresno, CA | 228 | 19 | 14 |
| 37860 | Pensacola-Ferry Pass-Brent, FL | 228 | 19 | 14 |
| 49660 | Youngstown-Warren, OH | 228 | 19 | 14 |
| 14740 | Bremerton-Silverdale-Port Orchard, WA | 229 | 18 | 14 |
| 15980 | Cape Coral-Fort Myers, FL | 229 | 19 | 14 |
| 14500 | Boulder, CO | 230 | 19 | 14 |
| 16220 | Casper, WY | 230 | 19 | 14 |
| 46540 | Utica-Rome, NY | 230 | 19 | 14 |
| 16940 | Cheyenne, WY | 231 | 19 | 14 |
| 29700 | Laredo, TX | 231 | 19 | 14 |
| 41100 | St. George, UT | 231 | 19 | 14 |
| 47300 | Visalia, CA | 231 | 19 | 14 |
| 15180 | Brownsville-Harlingen, TX | 232 | 19 | 14 |
| 11200 | Amherst Town-Northampton, MA | 233 | 19 | 14 |
| 19300 | Daphne-Fairhope-Foley, AL | 233 | 19 | 14 |
| 26380 | Houma-Bayou Cane-Thibodaux, LA | 234 | 19 | 14 |
| 35840 | North Port-Bradenton-Sarasota, FL | 234 | 19 | 14 |
| 18880 | Crestview-Fort Walton Beach-Destin, FL | 235 | 19 | 14 |
| 32780 | Medford, OR | 235 | 19 | 14 |
| 39150 | Prescott Valley-Prescott, AZ | 235 | 19 | 14 |
| 45940 | Trenton-Princeton, NJ | 235 | 19 | 14 |
| 46060 | Tucson, AZ | 235 | 19 | 14 |
| 49620 | York-Hanover, PA | 235 | 19 | 14 |
| 14580 | Bozeman, MT | 236 | 19 | 14 |
| 34820 | Myrtle Beach-Conway-North Myrtle Beach, SC | 236 | 19 | 14 |
| 34940 | Naples-Marco Island, FL | 236 | 19 | 14 |
| 11460 | Ann Arbor, MI | 237 | 19 | 14 |
| 37340 | Palm Bay-Melbourne-Titusville, FL | 237 | 19 | 14 |
| 43640 | Slidell-Mandeville-Covington, LA | 237 | 19 | 14 |
| 13380 | Bellingham, WA | 238 | 19 | 14 |
| 42140 | Santa Fe, NM | 238 | 19 | 14 |
| 46340 | Tyler, TX | 238 | 19 | 14 |
| 17020 | Chico, CA | 239 | 19 | 14 |
| 39740 | Reading, PA | 239 | 19 | 14 |
| 42020 | San Luis Obispo-Paso Robles, CA | 239 | 19 | 14 |
| 45300 | Tampa-St. Petersburg-Clearwater, FL | 239 | 19 | 14 |
| 46700 | Vallejo, CA | 239 | 19 | 14 |
| 49420 | Yakima, WA | 239 | 19 | 14 |
| 11260 | Anchorage, AK | 240 | 19 | 14 |
| 24300 | Grand Junction, CO | 240 | 19 | 14 |
| 32580 | McAllen-Edinburg-Mission, TX | 240 | 19 | 14 |
| 33660 | Mobile, AL | 240 | 19 | 14 |
| 17660 | Coeur d'Alene, ID | 241 | 19 | 14 |
| 36500 | Olympia-Lacey-Tumwater, WA | 241 | 19 | 14 |
| 37100 | Oxnard-Thousand Oaks-Ventura, CA | 241 | 19 | 14 |
| 31700 | Manchester-Nashua, NH | 242 | 19 | 14 |
| 22660 | Fort Collins-Loveland, CO | 243 | 19 | 14 |
| 24540 | Greeley, CO | 243 | 19 | 14 |
| 46520 | Urban Honolulu, HI | 243 | 19 | 14 |
| 29460 | Lakeland-Winter Haven, FL | 244 | 19 | 14 |
| 44700 | Stockton-Lodi, CA | 245 | 19 | 14 |
| 42220 | Santa Rosa-Petaluma, CA | 246 | 19 | 14 |
| 36740 | Orlando-Kissimmee-Sanford, FL | 247 | 19 | 14 |
| 40140 | Riverside-San Bernardino-Ontario, CA | 247 | 19 | 14 |
| 49340 | Worcester, MA | 247 | 19 | 14 |
| 29820 | Las Vegas-Henderson-North Las Vegas, NV | 249 | 19 | 14 |
| 38300 | Pittsburgh, PA | 249 | 19 | 14 |
| 42200 | Santa Maria-Santa Barbara, CA | 249 | 19 | 14 |
| 36100 | Ocala, FL | 251 | 19 | 14 |
| 42660 | Seattle-Tacoma-Bellevue, WA | 251 | 19 | 14 |
| 29540 | Lancaster, PA | 252 | 19 | 14 |
| 41740 | San Diego-Chula Vista-Carlsbad, CA | 252 | 19 | 14 |
| 12540 | Bakersfield-Delano, CA | 254 | 19 | 14 |
| 41500 | Salinas, CA | 255 | 19 | 14 |
| 21660 | Eugene-Springfield, OR | 257 | 19 | 14 |
| 38060 | Phoenix-Mesa-Chandler, AZ | 257 | 19 | 14 |
| 31080 | Los Angeles-Long Beach-Anaheim, CA | 265 | 19 | 14 |
| 33100 | Miami-Fort Lauderdale-West Palm Beach, FL | 265 | 19 | 14 |

## Variable Missingness

| Variable | Missing | Percent |
| --- | ---: | ---: |
| `startup_rate` | 0 | 0.00% |
| `startup_rate_lag1` | 8,683 | 13.66% |
| `startup_rate_lag2` | 12,978 | 20.41% |
| `startup_rate_lag3` | 17,171 | 27.01% |
| `firm_startups` | 0 | 0.00% |
| `establishment_entry` | 2,449 | 3.85% |
| `establishment_entry_rate` | 2,449 | 3.85% |
| `startup_job_creation` | 0 | 0.00% |
| `qcew_employment` | 0 | 0.00% |
| `qcew_establishments` | 0 | 0.00% |
| `qcew_payroll` | 0 | 0.00% |
| `qcew_average_wage` | 0 | 0.00% |
| `qcew_total_annual_wages_nominal` | 0 | 0.00% |
| `qcew_average_annual_pay_nominal` | 0 | 0.00% |
| `employment_growth` | 6,468 | 10.17% |
| `establishment_growth` | 6,468 | 10.17% |
| `payroll_growth` | 6,468 | 10.17% |
| `wage_growth` | 6,468 | 10.17% |
| `employment_growth_lag1` | 12,168 | 19.14% |
| `employment_growth_lag2` | 16,890 | 26.57% |
| `employment_growth_lag3` | 21,399 | 33.66% |
| `establishment_growth_lag1` | 12,168 | 19.14% |
| `establishment_growth_lag2` | 16,890 | 26.57% |
| `establishment_growth_lag3` | 21,399 | 33.66% |
| `payroll_growth_lag1` | 12,168 | 19.14% |
| `average_pay_growth_lag1` | 12,168 | 19.14% |
| `acs_population` | 3,538 | 5.56% |
| `acs_population_growth` | 8,062 | 12.68% |
| `acs_population_growth_lag1` | 12,414 | 19.53% |
| `median_household_income` | 3,538 | 5.56% |
| `median_household_income_lag1` | 8,062 | 12.68% |
| `educational_attainment_pct` | 3,538 | 5.56% |
| `educational_attainment_pct_lag1` | 8,062 | 12.68% |
| `labor_force_participation_pct` | 3,538 | 5.56% |
| `labor_force_participation_pct_lag1` | 8,062 | 12.68% |
| `unemployment_rate` | 3,538 | 5.56% |
| `unemployment_rate_lag1` | 8,062 | 12.68% |
| `cbp_establishments` | 5,341 | 8.40% |
| `cbp_employment` | 5,341 | 8.40% |
| `cbp_annual_payroll` | 5,341 | 8.40% |
| `cbp_first_quarter_payroll` | 5,341 | 8.40% |

## QCEW-CBP Consistency Diagnostics

These are descriptive comparisons, not equality requirements. QCEW employment is an annual average while CBP employment is a March reference-period count. QCEW payroll is in dollars and CBP payroll fields are in $1,000; CBP payroll is multiplied by 1,000 for these diagnostics only. Stored source values retain their native units. Coverage and reporting conventions may also differ.

| Measure | Matched | Correlation | Median CBP/QCEW | Median absolute pct. difference | >100% differences |
| --- | ---: | ---: | ---: | ---: | ---: |
| employment | 58,236 | 0.9932 | 1.0275 | 0.1064 | 1,075 |
| establishments | 58,236 | 0.7858 | 0.9773 | 0.0959 | 134 |
| payroll | 58,236 | 0.9834 | 0.9903 | 0.1085 | 1,082 |

For observations with more than 100% absolute difference, the year/sector/MSA breakdowns and the ten highest-count MSAs are available in the ignored generated JSON audit `reports/generated/a412_panel_audit.json`.

## Idempotency And Leakage Boundary

Build run c954f026-94d2-433f-b261-aff4f66bec44 wrote 63,577 rows. The runner clears and deterministically rebuilds only the analytics table; it refuses duplicate source keys and records run-scoped metrics. No expected entrepreneurship, alignment residual, gap label, future lead, or modeling field is created.


### Major Differences By Year, Sector, And MSA

**Employment** (groups ranked by observations with >100% absolute difference)

By Year: 2020 (140/4456); 2018 (94/4479); 2019 (90/4477); 2016 (85/4394); 2021 (81/4470)
By Sector: 55 (357/1628); 51 (156/2468); 61 (117/2072); 81 (107/4540); 21 (89/1123)
By Msa: 49740 (25/216); 26620 (19/181); 20100 (18/197); 45940 (18/231); 13020 (17/158)

**Establishments** (groups ranked by observations with >100% absolute difference)

By Year: 2015 (13/4388); 2017 (13/4384); 2020 (13/4456); 2010 (11/3661); 2014 (10/3631)
By Sector: 55 (71/1628); 51 (26/2468); 22 (17/1150); 21 (7/1123); 61 (6/2072)
By Msa: 28020 (14/213); 40980 (13/185); 20100 (11/197); 16220 (7/221); 34740 (7/171)

**Payroll** (groups ranked by observations with >100% absolute difference)

By Year: 2022 (97/4592); 2019 (96/4477); 2020 (90/4456); 2015 (88/4388); 2021 (87/4470)
By Sector: 55 (345/1628); 51 (162/2468); 21 (94/1123); 62 (60/3359); 71 (59/3007)
By Msa: 45940 (24/231); 22380 (21/213); 12980 (20/152); 22140 (20/202); 49740 (19/216)
