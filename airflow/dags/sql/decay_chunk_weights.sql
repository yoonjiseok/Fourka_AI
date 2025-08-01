-- 청크 가중치 decay 작업
-- 작성자: 데이터팀
-- 목적: ML 모델의 개인화 가중치를 주기적으로 감소시켜 최신성 반영

-- 실행 전 현재 상태 로깅
INSERT INTO decay_logs (execution_date, chunks_before_decay) 
SELECT 
    NOW() as execution_date,
    COUNT(*) as chunks_before_decay
FROM chunk 
WHERE weight > 1.0;

-- 1주일 이상 지난 청크들의 가중치를 5% 감소
-- 단, 최소 가중치는 1.0으로 유지 (기본값으로 복귀)
UPDATE chunk 
SET 
    weight = GREATEST(weight * 0.95, 1.0),
    updated_at = NOW()
WHERE 
    weight > 1.0 
    AND updated_at < NOW() - '7 days'::INTERVAL
    AND weight * 0.95 > 1.0;  -- 실제로 변경될 경우만

-- 실행 후 결과 로깅  
INSERT INTO decay_logs (execution_date, chunks_after_decay, affected_chunks)
SELECT 
    NOW() as execution_date,
    COUNT(*) FILTER (WHERE weight > 1.0) as chunks_after_decay,
    COUNT(*) FILTER (WHERE weight = 1.0 AND updated_at > NOW() - INTERVAL '1 minute') as affected_chunks
FROM chunk; 