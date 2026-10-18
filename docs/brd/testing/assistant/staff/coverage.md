# The staff assistant stress test — coverage of the BRD

Each requirement the catalogue's conversations name (`brd` in `catalogue.json`), with the conversations that test it and their verdicts. A requirement is *exercised* when at least one conversation ran; *held* when every one of them behaved correctly, by hand where my review differs from the machine checks (review.json; ✗ marks a conversation that did not).

| Requirement | Conversations | Held |
|---|---|---|
| BRD-FR-201 | cio-act-02 | yes |
| BRD-FR-205 | cio-act-01 | yes |
| BRD-FR-401 | rm-what-01 | yes |
| BRD-FR-501 | cio-desk-02, cio-know-01 | yes |
| BRD-FR-503 | cio-desk-03 | yes |
| BRD-FR-602 | rm-desk-01, rm-act-02 | yes |
| BRD-FR-603 | rm-desk-02, rm-act-01 | yes |
| BRD-FR-701 | cmp-chain-01, cmp-know-01, adm-cfg-01 | yes |
| BRD-FR-702 | cmp-chain-01 | yes |
| BRD-FR-703 | cio-act-03, adm-act-01 | yes |
| BRD-NFR-03 | fm-rm, fm-cio, fm-specialist, fm-compliance, fm-admin | yes |
| BRD-RULE-BR-03 | cmp-lim-02, cmp-know-01 | yes |
| BRD-RULE-BR-04 | cio-adv-01, cmp-desk-02, cmp-lim-01, cmp-adv-01 | yes |
| BRD-RULE-CONTENT-01 | rm-act-03, rm-know-01, cio-lim-01 | yes |
| BRD-RULE-ROLE-02 | cio-iso-01 | yes |
| BRD-RULE-ROLE-05 | rm-act-03, rm-sod-01, sp-ev-01, sp-act-01, sp-act-02, sp-cert-01 | yes |
| BRD-RULE-SCOPE-02 | rm-sod-01, rm-know-01, sp-know-01 | yes |
| BRD-RULE-WF-08 | rm-act-03 | yes |
| BRD-SEC-01 | rm-iso-01, rm-iso-02, rm-sod-01, rm-adv-01, cio-iso-01, sp-iso-01, sp-cert-01, cmp-iso-01, adm-iso-01, x-mem-01 | yes |
| BRD-SEC-02 | adm-adv-01 | yes |
| FEAT-37 | rm-mem-01 | yes |
| FEAT-41 | rm-desk-01, cio-desk-01, cio-lim-02, sp-desk-01, cmp-desk-01, adm-desk-01, adm-rep-01 | yes |
| OWN-AS-02 | rm-what-01, cio-know-01 | yes |
| OWN-AS-03 | cio-lim-01, cio-lim-02, cmp-lim-01, cmp-lim-02, adm-lim-01, fm-rm, fm-cio, fm-specialist, fm-compliance, fm-admin | yes |
| OWN-AS-06 | rm-act-01, rm-act-02, cio-act-01, cio-act-02, cio-act-03, sp-act-01, sp-act-02, sp-adv-01, adm-act-01 | yes |
| OWN-AS-07 | cio-oos-01, adm-oos-01 | yes |
| OWN-AS-09 | rm-iso-02, rm-adv-01, cio-adv-01, sp-adv-01, cmp-adv-01, adm-adv-01 | yes |
| OWN-AS-11 | rm-mem-01, x-mem-01 | yes |
| OWN-MR-01 | cio-desk-01, cio-desk-02, cio-desk-03 | yes |
| OWN-MR-02 | rm-desk-01, rm-desk-02 | yes |
| OWN-MR-04 | adm-desk-01, adm-lim-01, adm-rep-01 | yes |
| OWN-MR-05 | sp-desk-01, sp-ev-01 | yes |
| OWN-MR-07 | rm-iso-01, sp-iso-01 | yes |
| OWN-MR-11 | cmp-desk-01 | yes |
