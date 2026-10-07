package com.jobautomator.ratelimit;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.time.Duration;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ReactiveRateLimiterTest {

    @Test
    @DisplayName("Should acquire available token immediately without delay")
    void shouldAcquireImmediately() {
        ReactiveRateLimiter limiter = new ReactiveRateLimiter();

        StepVerifier.create(limiter.acquire(ServiceName.LINKEDIN_SCRAPING))
                .verifyComplete();
    }

    @Test
    @DisplayName("Should tryAcquire successfully when tokens available and return false when depleted")
    void shouldTryAcquireAccurately() {
        ReactiveRateLimiter limiter = new ReactiveRateLimiter();
        // Register small capacity bucket: 2 tokens per 60 seconds
        limiter.registerService("TEST_SERVICE", RateLimitConfig.of(2, Duration.ofSeconds(60)));

        // Consume 1st token
        StepVerifier.create(limiter.tryAcquire("TEST_SERVICE"))
                .expectNext(true)
                .verifyComplete();

        // Consume 2nd token
        StepVerifier.create(limiter.tryAcquire("TEST_SERVICE"))
                .expectNext(true)
                .verifyComplete();

        // 3rd attempt should return false (depleted)
        StepVerifier.create(limiter.tryAcquire("TEST_SERVICE"))
                .expectNext(false)
                .verifyComplete();
    }

    @Test
    @DisplayName("Should throttle reactive action through rate limiter non-blockingly")
    void shouldThrottleAction() {
        ReactiveRateLimiter limiter = new ReactiveRateLimiter();

        Mono<String> action = Mono.just("Action Completed");

        StepVerifier.create(limiter.throttle(ServiceName.OPENAI_API, action))
                .expectNext("Action Completed")
                .verifyComplete();
    }

    @Test
    @DisplayName("Should delay non-blockingly when tokens are depleted and refill quickly")
    void shouldDelayNonBlockinglyAndRefill() {
        ReactiveRateLimiter limiter = new ReactiveRateLimiter();
        // 1 token capacity, refill period 50 milliseconds
        limiter.registerService("FAST_SERVICE", RateLimitConfig.of(1, Duration.ofMillis(50)));

        // 1st consume
        StepVerifier.create(limiter.acquire("FAST_SERVICE")).verifyComplete();

        // 2nd consume must wait ~50ms, then complete without blocking
        long start = System.currentTimeMillis();
        StepVerifier.create(limiter.acquire("FAST_SERVICE"))
                .verifyComplete();
        long duration = System.currentTimeMillis() - start;

        assertThat(duration).isGreaterThanOrEqualTo(25);
    }

    @Test
    @DisplayName("Should reject invalid RateLimitConfig parameters")
    void shouldValidateRateLimitConfig() {
        assertThatThrownBy(() -> RateLimitConfig.of(0, Duration.ofSeconds(10)))
                .isInstanceOf(IllegalArgumentException.class);

        assertThatThrownBy(() -> RateLimitConfig.of(5, Duration.ofSeconds(0)))
                .isInstanceOf(IllegalArgumentException.class);

        assertThatThrownBy(() -> RateLimitConfig.of(5, null))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
