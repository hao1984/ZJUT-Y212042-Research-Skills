window.__VIS_PAYLOAD__ = {
  "schema_version": "paper_grounded_frontend_payload_v0.1",
  "created_at": "2026-06-04T00:36:56",
  "run_dir": "C:\\Users\\Maxh\\Desktop\\VisPaper\\runs\\paper_grounded_skill_tests\\bnnvis",
  "input": {
    "title": "BNNVis: Towards Visual Analytics for Bayesian Neural Networks",
    "type": "paper",
    "path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Appleby-2025-BNNVis-Towards-Visual-Analytics-for-Bayesian-Neural-Networks",
    "description": "为贝叶斯神经网络不确定性分析设计并生成一个支持模型比较、误差定位和解释证据联动的可运行前端可视分析系统。",
    "abstract": "Bayesian Neural Networks (BNNs) offer a principled approach to modeling uncertainty in addition to providing predictions, making them particularly valuable for high-stake domains where uncertainty quantification is required. However, their adoption remains low, partly due to the difficulty in tuning and interpreting these models and their results. To address this limitation, we introduce BNNVis, a visual analytics tool designed to visualize BNNs and their results. BNNVis a...",
    "data_schema_columns": []
  },
  "domain_id": "model_uncertainty_diagnosis",
  "analysis_target": {
    "name": "BNNVis: Towards Visual Analytics for Bayesian Neural Networks uncertainty and prediction-error workspace",
    "supporting_patterns": [
      "predictions",
      "uncertainty",
      "model_components",
      "case_evidence"
    ],
    "primary_patterns": [
      "uncertain cases",
      "error clusters",
      "model comparison"
    ],
    "evidence_patterns": [
      "retrieved uncertainty-vis systems",
      "paper snippets",
      "case-level explanation traces"
    ],
    "operational_definition": {
      "entity": "sample, class, model/layer, uncertainty estimate, or error cluster",
      "grain": "one prediction case, one uncertainty group, or one model comparison cell",
      "states": [
        "selected_case",
        "selected_model",
        "selected_class",
        "selected_evidence_route"
      ],
      "primary_user_actions": [
        "select an uncertain case",
        "compare model/class behavior",
        "inspect explanation evidence",
        "trace error causes"
      ],
      "success_observations": [
        "user can identify which cases are uncertain, how errors cluster, and what model evidence explains them"
      ],
      "excluded_interpretations": [
        "not a leaderboard",
        "not a single confusion matrix",
        "not a KPI dashboard"
      ]
    }
  },
  "primary_question": "How can analysts compare prediction behavior, uncertainty, and case-level explanations in BNNVis: Towards Visual Analytics for Bayesian Neural Networks?",
  "primary_visual_object": "A model-diagnosis workspace where uncertain cases, model/class comparisons, explanation traces, and paper-grounded design patterns are linked.",
  "view_graph": [
    {
      "view_id": "case_uncertainty_view",
      "role": "primary",
      "purpose": "Show prediction cases or clusters positioned by uncertainty, error type, and selected class/model context.",
      "reference_grounding": "hybrid relation overview: use a graph/matrix companion to expose entity relations and reduce single-view ambiguity"
    },
    {
      "view_id": "model_class_matrix",
      "role": "companion",
      "purpose": "Compare models, classes, or layers with error and uncertainty highlighting.",
      "reference_grounding": "uncertainty layer as secondary evidence, revealed through selection rather than default KPI summaries"
    },
    {
      "view_id": "case_explanation_view",
      "role": "companion",
      "purpose": "Show selected posterior, feature/layer attribution, or disagreement traces for the active case.",
      "reference_grounding": "spatial semantic structure view with selectable regions/components and linked detail evidence"
    },
    {
      "view_id": "evidence_panel",
      "role": "detail",
      "purpose": "Show paper snippets, provenance, caveats, and the current diagnostic rationale.",
      "reference_grounding": "standard evidence trace policy"
    }
  ],
  "shared_state": [
    "selected_case",
    "selected_model",
    "selected_class",
    "selected_evidence_route"
  ],
  "linked_interactions": [
    {
      "interaction_id": "select_case_updates_diagnosis",
      "source_view": "case_uncertainty_view",
      "target_views": [
        "model_class_matrix",
        "case_explanation_view",
        "evidence_panel"
      ],
      "shared_state": "selected_case"
    },
    {
      "interaction_id": "select_model_class_filters_cases",
      "source_view": "model_class_matrix",
      "target_views": [
        "case_uncertainty_view",
        "case_explanation_view",
        "evidence_panel"
      ],
      "shared_state": "selected_model"
    },
    {
      "interaction_id": "select_explanation_updates_evidence",
      "source_view": "case_explanation_view",
      "target_views": [
        "case_uncertainty_view",
        "evidence_panel"
      ],
      "shared_state": "selected_evidence_route"
    }
  ],
  "guided_open_exploration": {
    "model": "guided_open_exploration",
    "default_state": "Show the highest-uncertainty cases, model/class relation overview, and one explanation route for the top selected case.",
    "entry_points": [
      "start from uncertain case",
      "start from model/class comparison",
      "start from explanation evidence"
    ],
    "analysis_routes": [
      "uncertain case -> model/class context -> explanation evidence",
      "class anomaly -> case cluster -> uncertainty distribution",
      "reference pattern -> adapted diagnosis interaction -> caveat"
    ],
    "non_linear_guards": [
      "clear selection is always visible",
      "aggregate metrics never replace case-level evidence",
      "uncertainty encodings stay linked to cases"
    ]
  },
  "viewport_contract": {
    "primary_viewport": "1920x1080",
    "validation_viewport": "1440x810",
    "page_level_scroll": "forbidden_on_initial_load",
    "local_scroll": "allowed_inside_bounded_evidence_panels",
    "required_first_screen_view_ids": [
      "case_uncertainty_view",
      "model_class_matrix",
      "case_explanation_view",
      "evidence_panel"
    ]
  },
  "visual_style_system": {
    "style_intent": "model-diagnosis workspace with precise uncertainty marks, compact comparison structure, and calm evidence surfaces",
    "background_policy": "neutral light or cool gray; avoid generic ML dashboard styling and purple glow",
    "palette_roles": {
      "error": "clear warm accent",
      "uncertainty": "ordered blue-green or viridis-like ramp",
      "reference_grounding": "secondary cool hue",
      "evidence": "muted support tone"
    },
    "forbidden_styles_checked": [
      "beige/cream/sand",
      "paper grid",
      "generic dark KPI dashboard",
      "purple gradient/glow/blur"
    ],
    "typography_policy": "compact labels, no hero text, stable panel headings",
    "density_policy": "desktop analytical density with bounded local scroll"
  },
  "keywords": [
    {
      "id": "kw-1",
      "keyword": "visual analytics",
      "rank": 1,
      "weight": 20,
      "group": "model"
    },
    {
      "id": "kw-2",
      "keyword": "uncertainty visualization",
      "rank": 2,
      "weight": 17,
      "group": "uncertainty"
    },
    {
      "id": "kw-3",
      "keyword": "matrix",
      "rank": 3,
      "weight": 16,
      "group": "uncertainty"
    },
    {
      "id": "kw-4",
      "keyword": "bayesian neural network",
      "rank": 4,
      "weight": 17,
      "group": "uncertainty"
    },
    {
      "id": "kw-5",
      "keyword": "bnnvis",
      "rank": 5,
      "weight": 19,
      "group": "model"
    },
    {
      "id": "kw-6",
      "keyword": "uncertainty",
      "rank": 6,
      "weight": 15,
      "group": "uncertainty"
    },
    {
      "id": "kw-7",
      "keyword": "bnns",
      "rank": 7,
      "weight": 15,
      "group": "model"
    },
    {
      "id": "kw-8",
      "keyword": "neural",
      "rank": 8,
      "weight": 13,
      "group": "uncertainty"
    },
    {
      "id": "kw-9",
      "keyword": "how",
      "rank": 9,
      "weight": 13,
      "group": "model"
    },
    {
      "id": "kw-10",
      "keyword": "predictions",
      "rank": 10,
      "weight": 12,
      "group": "uncertainty"
    },
    {
      "id": "kw-11",
      "keyword": "analytics",
      "rank": 11,
      "weight": 10,
      "group": "model"
    },
    {
      "id": "kw-12",
      "keyword": "bayesian",
      "rank": 12,
      "weight": 9,
      "group": "uncertainty"
    },
    {
      "id": "kw-13",
      "keyword": "networks",
      "rank": 13,
      "weight": 8,
      "group": "model"
    },
    {
      "id": "kw-14",
      "keyword": "these",
      "rank": 14,
      "weight": 7,
      "group": "model"
    },
    {
      "id": "kw-15",
      "keyword": "bnn",
      "rank": 15,
      "weight": 14,
      "group": "model"
    },
    {
      "id": "kw-16",
      "keyword": "understand",
      "rank": 16,
      "weight": 5,
      "group": "model"
    },
    {
      "id": "kw-17",
      "keyword": "distributions",
      "rank": 17,
      "weight": 4,
      "group": "model"
    },
    {
      "id": "kw-18",
      "keyword": "architecture",
      "rank": 18,
      "weight": 2,
      "group": "model"
    }
  ],
  "references": [
    {
      "id": "8cecbf4a-f69f-414b-853f-0c5ebbb9f088",
      "rank": 1,
      "title": "ScatterUQ: Interactive Uncertainty Visualizations for Multiclass Deep Learning Problems",
      "short_title": "ScatterUQ: Interactive Uncertainty Visualizations for M...",
      "year": 2023,
      "journal": "2023 IEEE Visualization and Visual Analytics (VIS)",
      "score": 0.090909,
      "keyword_hits": 6,
      "abstract_snippet": "Recently, uncertainty-aware deep learning methods for multiclass labeling problems have been developed that provide calibrated class prediction probabilities and out-of-distribution (OOD) indicators, letting machine learning (ML) consumers and engineers gauge a model’s confidence in its predictions. However, this extra neural network prediction informatio...",
      "l3_snippet": "We have presented ScatterUQ, a visualization system designed to complement distance- and uncertainty-aware, multiclass neural networks and provide context-driven visualizations for three different usage scenarios. By focusing on local visualizations, ScatterUQ can scale to arbitrarily many classes and data sizes. Its confidence sliders allow it to fluidly adapt to a user’s requirements. A quantitative comparison i...",
      "meta_path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Li-2023-ScatterUQ-Interactive-Uncertainty-Visualizations-for-Multiclass-Deep-Learning-Problems\\meta.json",
      "paper_md_path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Li-2023-ScatterUQ-Interactive-Uncertainty-Visualizations-for-Multiclass-Deep-Learning-Problems\\paper.md",
      "borrowed_elements": [
        {
          "borrowed_element": "hybrid relation overview: use a graph/matrix companion to expose entity relations and reduce single-view ambiguity",
          "mapped_to_view_ids": [
            "relation_overview",
            "primary_structure_view"
          ],
          "mapped_to_interaction_ids": [
            "brush_relation_updates_primary"
          ],
          "confidence": "medium"
        },
        {
          "borrowed_element": "uncertainty layer as secondary evidence, revealed through selection rather than default KPI summaries",
          "mapped_to_view_ids": [
            "uncertainty_evidence_view",
            "evidence_panel"
          ],
          "mapped_to_interaction_ids": [
            "select_item_reveals_uncertainty"
          ],
          "confidence": "medium"
        }
      ]
    },
    {
      "id": "5c474e6d-da59-47df-9418-63a4116ac0eb",
      "rank": 2,
      "title": "Regularized Multi-Decoder Ensemble for an Error-Aware Scene Representation Network",
      "short_title": "Regularized Multi-Decoder Ensemble for an Error-Aware S...",
      "year": 2025,
      "journal": "IEEE Transactions on Visualization and Computer Graphics",
      "score": 0.083333,
      "keyword_hits": 3,
      "abstract_snippet": "Feature grid Scene Representation Networks (SRNs) have been applied to scientific data as compact functional surrogates for analysis and visualization. As SRNs are black-box lossy data representations, assessing the prediction quality is critical for scientific visualization applications to ensure that scientists can trust the information being visualized...",
      "l3_snippet": "To equip feature grid SRNs for scientific data with inference time prediction quality assessment, we propose RMDSRN that provides prediction variance quantification from multiple plausible predictions made to any given input coordinate for error-aware reconstruction of volumetric data. RMDSRN comprises a parameter-efficient multidecoder architecture synergized with a novel variance regularization loss for reliable...",
      "meta_path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Xiong-2025-Regularized-Multi-Decoder-Ensemble-for-an-Error-Aware-Scene-Representation-Network\\meta.json",
      "paper_md_path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Xiong-2025-Regularized-Multi-Decoder-Ensemble-for-an-Error-Aware-Scene-Representation-Network\\paper.md",
      "borrowed_elements": [
        {
          "borrowed_element": "spatial semantic structure view with selectable regions/components and linked detail evidence",
          "mapped_to_view_ids": [
            "primary_structure_view",
            "component_detail_view"
          ],
          "mapped_to_interaction_ids": [
            "select_component_updates_detail"
          ],
          "confidence": "high"
        },
        {
          "borrowed_element": "hybrid relation overview: use a graph/matrix companion to expose entity relations and reduce single-view ambiguity",
          "mapped_to_view_ids": [
            "relation_overview",
            "primary_structure_view"
          ],
          "mapped_to_interaction_ids": [
            "brush_relation_updates_primary"
          ],
          "confidence": "medium"
        }
      ]
    },
    {
      "id": "5a844ccd-8867-41a4-bd20-cc874c665d5c",
      "rank": 3,
      "title": "<i>GNNLens</i>\n                    : A Visual Analytics Approach for Prediction Error Diagnosis of Graph Neural Networks",
      "short_title": "GNNLens : A Visual Analytics Approach for Prediction Er...",
      "year": 2023,
      "journal": "IEEE Transactions on Visualization and Computer Graphics",
      "score": 0.076923,
      "keyword_hits": 5,
      "abstract_snippet": "Graph Neural Networks (GNNs) aim to extend deep learning techniques to graph data and have achieved significant progress in graph analysis tasks (e.g., node classification) in recent years. However, similar to other deep neural networks like Convolutional Neural Networks (CNNs) and Recurrent Neural Networks (RNNs), GNNs behave like a black box with their...",
      "l3_snippet": "",
      "meta_path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Jin-2023-iGNNLensi-A-Visual-Analytics-Approach-for-Prediction-Error-Diagnosis-of-Graph-Neural-Networks\\meta.json",
      "paper_md_path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Jin-2023-iGNNLensi-A-Visual-Analytics-Approach-for-Prediction-Error-Diagnosis-of-Graph-Neural-Networks\\paper.md",
      "borrowed_elements": [
        {
          "borrowed_element": "hybrid relation overview: use a graph/matrix companion to expose entity relations and reduce single-view ambiguity",
          "mapped_to_view_ids": [
            "relation_overview",
            "primary_structure_view"
          ],
          "mapped_to_interaction_ids": [
            "brush_relation_updates_primary"
          ],
          "confidence": "medium"
        }
      ]
    },
    {
      "id": "ca64b6e6-6f2c-4acf-8a19-64553fd83586",
      "rank": 4,
      "title": "Uncertainty-Aware Deep Neural Representations for Visual Analysis of Vector Field Data",
      "short_title": "Uncertainty-Aware Deep Neural Representations for Visua...",
      "year": 2025,
      "journal": "IEEE Transactions on Visualization and Computer Graphics",
      "score": 0.071429,
      "keyword_hits": 6,
      "abstract_snippet": "The widespread use of Deep Neural Networks (DNNs) has recently resulted in their application to challenging scientific visualization tasks. While advanced DNNs demonstrate impressive generalization abilities, understanding factors like prediction quality, confidence, robustness, and uncertainty is crucial. These insights aid application scientists in maki...",
      "l3_snippet": "This paper emphasizes the importance of understanding uncertainty by applying two uncertainty estimation methods. While in this work, we study the impact of uncertainty on tasks such as vector data prediction, streamline generation, and critical point detection, in the future, we plan to conduct a comprehensive topological analysis and thoroughly study flow map characteristics to evaluate reconstruction quality fu...",
      "meta_path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Kumar-2025-Uncertainty-Aware-Deep-Neural-Representations-for-Visual-Analysis-of-Vector-Field-Data\\meta.json",
      "paper_md_path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Kumar-2025-Uncertainty-Aware-Deep-Neural-Representations-for-Visual-Analysis-of-Vector-Field-Data\\paper.md",
      "borrowed_elements": [
        {
          "borrowed_element": "hybrid relation overview: use a graph/matrix companion to expose entity relations and reduce single-view ambiguity",
          "mapped_to_view_ids": [
            "relation_overview",
            "primary_structure_view"
          ],
          "mapped_to_interaction_ids": [
            "brush_relation_updates_primary"
          ],
          "confidence": "medium"
        },
        {
          "borrowed_element": "phase/time strip linked to the primary structure so users can compare temporal states without losing context",
          "mapped_to_view_ids": [
            "phase_strip_view",
            "primary_structure_view"
          ],
          "mapped_to_interaction_ids": [
            "brush_time_updates_structure"
          ],
          "confidence": "medium"
        }
      ]
    },
    {
      "id": "eafe7453-7182-4b6b-ac82-023a45147ae1",
      "rank": 5,
      "title": "ggdist: Visualizations of Distributions and Uncertainty in the Grammar of Graphics",
      "short_title": "ggdist: Visualizations of Distributions and Uncertainty...",
      "year": 2023,
      "journal": "IEEE Transactions on Visualization and Computer Graphics",
      "score": 0.066667,
      "keyword_hits": 4,
      "abstract_snippet": "The grammar of graphics is ubiquitous, providing the foundation for a variety of popular visualization tools and toolkits. Yet support for uncertainty visualization in the grammar graphics—beyond simple variations of error bars, uncertainty bands, and density plots—remains rudimentary. Research in uncertainty visualization has developed a rich variety of...",
      "l3_snippet": "ggdist has been a six-year journey in implementing a distributional, petty-statistics-camp-agnostic approach to uncertainty visualization in the grammar of graphics. While there remain many interesting future challenges to integrating further classes of uncertainty visualizations under one umbrella, the flexibility and expressiveness of ggdist thus far demonstrates the power of its underlying abstractions. Taking...",
      "meta_path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Kay-2023-ggdist-Visualizations-of-Distributions-and-Uncertainty-in-the-Grammar-of-Graphics\\meta.json",
      "paper_md_path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Kay-2023-ggdist-Visualizations-of-Distributions-and-Uncertainty-in-the-Grammar-of-Graphics\\paper.md",
      "borrowed_elements": [
        {
          "borrowed_element": "hybrid relation overview: use a graph/matrix companion to expose entity relations and reduce single-view ambiguity",
          "mapped_to_view_ids": [
            "relation_overview",
            "primary_structure_view"
          ],
          "mapped_to_interaction_ids": [
            "brush_relation_updates_primary"
          ],
          "confidence": "medium"
        },
        {
          "borrowed_element": "phase/time strip linked to the primary structure so users can compare temporal states without losing context",
          "mapped_to_view_ids": [
            "phase_strip_view",
            "primary_structure_view"
          ],
          "mapped_to_interaction_ids": [
            "brush_time_updates_structure"
          ],
          "confidence": "medium"
        }
      ]
    },
    {
      "id": "898c78ae-f9db-4cb4-a2bf-4138c34f8a11",
      "rank": 6,
      "title": "Trust Your Gut: Comparing Human and Machine Inference from Noisy Visualizations",
      "short_title": "Trust Your Gut: Comparing Human and Machine Inference f...",
      "year": 2025,
      "journal": "IEEE Transactions on Visualization and Computer Graphics",
      "score": 0.0625,
      "keyword_hits": 2,
      "abstract_snippet": "People commonly utilize visualizations not only to examine a given dataset, but also to draw generalizable conclusions about the underlying models or phenomena. Prior research has compared human visual inference to that of an optimal Bayesian agent, with deviations from rational analysis viewed as problematic. However, human reliance on non-normative heur...",
      "l3_snippet": "We investigated human inference-making from (at times noisy) visualizations, contrasting the accuracy of human judgments with those of Bayesian agents. Our central hypothesis was that, while humans exhibit non-rational tendencies, they may possess advantages in certain scenarios. The experiment findings support this notion: Although participants were generally less optimal than Bayesian benchmarks, they surpassed...",
      "meta_path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Koonchanok-2025-Trust-Your-Gut-Comparing-Human-and-Machine-Inference-from-Noisy-Visualizations\\meta.json",
      "paper_md_path": "C:\\Users\\Maxh\\Desktop\\VisPaper\\data\\papers\\Koonchanok-2025-Trust-Your-Gut-Comparing-Human-and-Machine-Inference-from-Noisy-Visualizations\\paper.md",
      "borrowed_elements": [
        {
          "borrowed_element": "intent-to-action trace: pair a natural-language/semantic control with an explicit execution/evidence view",
          "mapped_to_view_ids": [
            "intent_trace_view",
            "evidence_panel"
          ],
          "mapped_to_interaction_ids": [
            "intent_updates_workspace"
          ],
          "confidence": "high"
        },
        {
          "borrowed_element": "phase/time strip linked to the primary structure so users can compare temporal states without losing context",
          "mapped_to_view_ids": [
            "phase_strip_view",
            "primary_structure_view"
          ],
          "mapped_to_interaction_ids": [
            "brush_time_updates_structure"
          ],
          "confidence": "medium"
        }
      ]
    }
  ],
  "retrieval": {
    "status": "ok",
    "mode": "fts_only",
    "query": "visual analytics uncertainty visualization matrix bayesian neural network bnnvis uncertainty bnns neural how predictions",
    "coverage_summary": {
      "selected_reference_count": 6,
      "applied_paper_count": 6,
      "explicitly_rejected_paper_count": 0,
      "silent_reference_count": 0
    }
  },
  "contract_snapshot": {
    "why_not_dashboard": "The work is model diagnosis: users must move between uncertain cases, class/model relations, distributions, and explanation evidence. A dashboard of aggregate accuracy metrics would hide these links.",
    "data_task_encoding_mapping": [
      {
        "field_or_concept": "prediction cases",
        "task": "locate errors and ambiguous outcomes",
        "encoding": "case map or ranked uncertainty strip with selection-linked details",
        "reason": "model diagnosis begins with concrete cases rather than aggregate scores"
      },
      {
        "field_or_concept": "uncertainty distributions",
        "task": "compare confidence, posterior spread, or disagreement",
        "encoding": "distribution glyphs or interval bands tied to selected class/model",
        "reason": "uncertainty must be shown as structure, not collapsed into one number"
      },
      {
        "field_or_concept": "model/class relationships",
        "task": "diagnose where predictions diverge",
        "encoding": "model-class matrix or relation overview with error highlighting",
        "reason": "comparison across model components reveals systematic failure modes"
      },
      {
        "field_or_concept": "explanation evidence",
        "task": "connect a selected case to the reason it is uncertain or wrong",
        "encoding": "bounded evidence panel with feature, layer, or source snippets",
        "reason": "analysts need traceable evidence before trusting diagnosis"
      }
    ]
  },
  "default_selection": {
    "reference_id": "8cecbf4a-f69f-414b-853f-0c5ebbb9f088",
    "keyword_id": "kw-1",
    "route": "structure"
  }
};
