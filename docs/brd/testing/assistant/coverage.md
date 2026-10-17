# The assistant stress test — coverage of the BRD

Each requirement the catalogue's conversations name (`brd` in `catalogue.json`), with the conversations that test it and their verdicts. A requirement is *exercised* when at least one conversation ran; *held* when every one of them behaved correctly, by hand where my review differs from the machine checks (review.json; ✗ marks a conversation that did not).

| Requirement | Conversations | Held |
|---|---|---|
| BR-08 | nw-01, nw-03 | yes |
| BRD-NFR-03 | fm-01, fm-02, fm-03, fm-07 | yes |
| BRD-RULE-CONTENT-02 | kn-01, nw-01 | yes |
| BRD-RULE-ROLE-02 | adv-04 | yes |
| BRD-RULE-SCOPE-02 | pf-03, kn-01, wi-06, cc-05 | yes |
| BRIEF-DASH-01 | pf-01, pf-03, pf-05 | yes |
| BRIEF-DASH-02 | pf-04 | yes |
| BRIEF-DASH-04 | pf-04 | yes |
| BRIEF-DASH-05 | pf-06, gl-03 | yes |
| BRIEF-DATA-01 | nav-05 | yes |
| BRIEF-IMPACT-01 | nw-04 | yes |
| BRIEF-SCEN-01 | gl-01, gl-02, gl-04, wi-06 | yes |
| BRIEF-SCEN-02 | wi-01, wi-03, wi-04 | yes |
| FEAT-09 | nw-02 | yes |
| FEAT-20 | pf-05 | yes |
| FEAT-25 | nw-04 | yes |
| FEAT-26 | gl-01, cc-03 | yes |
| FEAT-37 | fm-06 | yes |
| FR-603 | act-04, act-05, fm-03, fm-07 | yes |
| KIT-COPILOT-01 | nav-03 | yes |
| KIT-COPILOT-02 | nav-01 ✗, nav-02, nav-04, pf-02, act-09, ms-01, am-04, am-05 | no (1) |
| KIT-COPILOT-03 | act-08, adv-09 | yes |
| KIT-COPILOT-04 | adv-01, adv-02, adv-03, adv-06, adv-07, adv-08 | yes |
| KIT-COPILOT-05 | nav-02, pf-01, pf-07, kn-02, kn-03, kn-06, nw-01, nw-05, gl-02, gl-04, wi-03, wi-04, wi-05, cc-01, cc-02, cc-03, cc-04, cc-05, act-06, ms-02, am-01, am-02, adv-05, fm-01, fm-02, fm-05 | yes |
| KIT-COPILOT-06 | act-01, act-02, act-03, act-04, act-05, adv-07, adv-09, fm-01, fm-02, fm-03 | yes |
| OWN-AS-01 | act-09 | yes |
| OWN-AS-02 | nav-01 ✗, nav-02, nav-04, nav-05 | no (1) |
| OWN-AS-03 | pf-01, pf-02, pf-03, pf-04, pf-05, pf-06, kn-05, nw-03, gl-05, cc-01, cc-02, ms-06, am-02, adv-02, adv-04, adv-07, fm-05 | yes |
| OWN-AS-05 | act-01, act-04, act-05, am-04 | yes |
| OWN-AS-06 | act-01, act-02, act-03, act-04, act-05, adv-09, fm-03, fm-07 | yes |
| OWN-AS-07 | kn-01, kn-02, kn-03, kn-04, kn-05, kn-06, nw-05, gl-03, gl-05, oos-01, oos-02, oos-05, fm-04 | yes |
| OWN-AS-08 | pf-07, gl-02, wi-05, act-06, act-07, act-08, oos-01, oos-03, oos-04, fm-04 | yes |
| OWN-AS-11 | ms-01, ms-02, ms-04, am-03, fm-06 | yes |
| OWN-AS-12 | act-01, ms-02, ms-05 | yes |
| OWN-AS-13 | ms-03 | yes |
| OWN-AS-14 | act-01, act-02 | yes |
| OWN-AS-15 | act-02 | yes |
| OWN-AS-16 | ms-05, ms-06, adv-02, adv-08 | yes |
| OWN-AS-18 | act-03 | yes |
| OWN-GW-36 | gl-01 | yes |
| OWN-GW-38 | nav-01 ✗, nav-06, wi-01 | no (1) |
| OWN-GW-40 | wi-01, wi-02 | yes |
| OWN-GW-42 | nw-02 | yes |
| OWN-GW-45 | nav-03, wi-02 | yes |
| OWN-GW-46 | nav-06 | yes |
| OWN-GW-47 | nav-03, nav-06, nw-02, wi-02, act-07, adv-03 | yes |
| OWN-SS-03 | ms-03 | yes |
| OWN-SS-05 | ms-04, fm-06 | yes |
