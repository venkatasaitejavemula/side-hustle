--
-- PostgreSQL database dump
--

\restrict eraU95M6qsp9HaSKkalbxOeYC5CCnGDVZuS3BNKY625Tur3qxWSDMJOiQR3w2w6

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: model_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_metrics (
    id integer NOT NULL,
    eval_date date NOT NULL,
    total_predictions integer,
    target_hit integer,
    sl_hit integer,
    no_entry integer,
    stagnant integer,
    win_rate real,
    retrained integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: model_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.model_metrics_id_seq OWNED BY public.model_metrics.id;


--
-- Name: model_params; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_params (
    param_name text NOT NULL,
    param_value real NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: predictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.predictions (
    id integer NOT NULL,
    prediction_date date NOT NULL,
    target_date date NOT NULL,
    stock text NOT NULL,
    predicted_entry real NOT NULL,
    predicted_target real NOT NULL,
    predicted_sl real NOT NULL,
    actual_open real,
    actual_high real,
    actual_low real,
    actual_close real,
    actual_volume integer,
    outcome text,
    reason text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: predictions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.predictions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: predictions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.predictions_id_seq OWNED BY public.predictions.id;


--
-- Name: model_metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_metrics ALTER COLUMN id SET DEFAULT nextval('public.model_metrics_id_seq'::regclass);


--
-- Name: predictions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions ALTER COLUMN id SET DEFAULT nextval('public.predictions_id_seq'::regclass);


--
-- Data for Name: model_metrics; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.model_metrics (id, eval_date, total_predictions, target_hit, sl_hit, no_entry, stagnant, win_rate, retrained, created_at) FROM stdin;
1	2026-02-11	5	0	0	0	5	0	1	2026-02-11 11:46:15.897974
\.


--
-- Data for Name: model_params; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.model_params (param_name, param_value, updated_at) FROM stdin;
atr_multiplier	1.5	2026-02-10 14:06:49.291116
risk_reward_ratio	2	2026-02-10 14:06:49.291116
score_threshold	4	2026-02-10 14:06:49.291116
prediction_count	5	2026-02-10 14:06:49.291116
\.


--
-- Data for Name: predictions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.predictions (id, prediction_date, target_date, stock, predicted_entry, predicted_target, predicted_sl, actual_open, actual_high, actual_low, actual_close, actual_volume, outcome, reason, created_at) FROM stdin;
6	2026-02-11	2026-02-12	GRAPHITE.NS	678.14	777.02	628.7	\N	\N	\N	\N	\N	\N	\N	2026-02-11 11:36:00.877295
7	2026-02-11	2026-02-12	HEROMOTOCO.NS	5777.39	6234.97	5548.6	\N	\N	\N	\N	\N	\N	\N	2026-02-11 11:36:00.877295
8	2026-02-11	2026-02-12	ESCORTS.NS	3872.3	4287.56	3664.67	\N	\N	\N	\N	\N	\N	\N	2026-02-11 11:36:00.877295
9	2026-02-11	2026-02-12	ASTRAL.NS	1545.63	1679.91	1478.49	\N	\N	\N	\N	\N	\N	\N	2026-02-11 11:36:00.877295
10	2026-02-11	2026-02-12	NMDC.NS	86.39	95.67	81.75	\N	\N	\N	\N	\N	\N	\N	2026-02-11 11:36:00.877295
1	2026-02-10	2026-02-11	SBIN.NS	1155.88	1254.68	1106.48	1142.8	1187.3	1142.8	1181.1	28939213	STAGNANT	Low volatility. Entry was triggered at Γé╣1155.88 but the stock closed at Γé╣1181.0999755859375 (+2.18%), failing to reach either target (Γé╣1254.68) or stop-loss (Γé╣1106.48). Volume: very high volume (2x+ average); Trend: strong uptrend (EMA9 widening above EMA21). Market lacked the power to push the stock to the target before closing. Late-session breakout confirmed strength.	2026-02-10 14:08:50.896607
2	2026-02-10	2026-02-11	TITAN.NS	4288.6	4596.62	4134.59	4350.2	4368.4	4208.5	4238	2768682	STAGNANT	Low volatility. Entry was triggered at Γé╣4288.6 but the stock closed at Γé╣4238.0 (-1.18%), failing to reach either target (Γé╣4596.62) or stop-loss (Γé╣4134.59). Volume: very high volume (2x+ average); Trend: strong uptrend (EMA9 widening above EMA21). Market lacked the power to push the stock to the target before closing. Opening spike followed by sustained selling.	2026-02-10 14:08:50.896607
3	2026-02-10	2026-02-11	TATASTEEL.NS	206.34	226.88	196.07	209.35	210.25	205.31	207.5	37800437	STAGNANT	Low volatility. Entry was triggered at Γé╣206.34 but the stock closed at Γé╣207.5 (+0.56%), failing to reach either target (Γé╣226.88) or stop-loss (Γé╣196.07). Volume: average volume; Trend: strong uptrend (EMA9 widening above EMA21). Insufficient participation to sustain momentum. Market lacked the power to push the stock to the target before closing. Opening spike followed by sustained selling.	2026-02-10 14:08:50.896607
4	2026-02-10	2026-02-11	BLUESTARCO.NS	1958.96	2178.56	1849.16	1959	1965.7	1934.2	1958.6	365215	STAGNANT	Low volatility. Entry was triggered at Γé╣1958.96 but the stock closed at Γé╣1958.5999755859375 (-0.02%), failing to reach either target (Γé╣2178.56) or stop-loss (Γé╣1849.16). Volume: below-average volume; Trend: strong uptrend (EMA9 widening above EMA21). Insufficient participation to sustain momentum. Market lacked the power to push the stock to the target before closing.	2026-02-10 14:08:50.896607
5	2026-02-10	2026-02-11	TORNTPOWER.NS	1445	1577.84	1378.58	1465.2	1465.2	1385.3	1428.6	2838049	STAGNANT	Low volatility. Entry was triggered at Γé╣1445.0 but the stock closed at Γé╣1428.5999755859375 (-1.13%), failing to reach either target (Γé╣1577.84) or stop-loss (Γé╣1378.58). Volume: very high volume (2x+ average); Trend: strong uptrend (EMA9 widening above EMA21). Market lacked the power to push the stock to the target before closing. Opening spike followed by sustained selling.	2026-02-10 14:08:50.896607
\.


--
-- Name: model_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.model_metrics_id_seq', 1, true);


--
-- Name: predictions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.predictions_id_seq', 10, true);


--
-- Name: model_metrics model_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_metrics
    ADD CONSTRAINT model_metrics_pkey PRIMARY KEY (id);


--
-- Name: model_params model_params_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_params
    ADD CONSTRAINT model_params_pkey PRIMARY KEY (param_name);


--
-- Name: predictions predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_pkey PRIMARY KEY (id);


--
-- Name: predictions predictions_target_date_stock_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_target_date_stock_key UNIQUE (target_date, stock);


--
-- PostgreSQL database dump complete
--

\unrestrict eraU95M6qsp9HaSKkalbxOeYC5CCnGDVZuS3BNKY625Tur3qxWSDMJOiQR3w2w6

