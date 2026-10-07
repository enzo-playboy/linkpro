package com.jobautomator;

import com.jobautomator.ratelimit.ReactiveRateLimiter;
import io.agentscope.core.message.TextBlock;
import io.agentscope.core.model.ChatResponse;
import io.agentscope.extensions.model.openai.OpenAIChatModel;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class LinkedInProfileScannerAgentTest {

    @Mock
    private OpenAIChatModel chatModel;

    private LinkedInProfileScannerAgent agent;

    @BeforeEach
    void setUp() {
        agent = new LinkedInProfileScannerAgent(chatModel, new ReactiveRateLimiter());
    }

    @Test
    @DisplayName("Should scan profile successfully and return analysis recommendations")
    void shouldScanProfileSuccessfully() {
        ChatResponse mockResponse = ChatResponse.builder()
                .content(List.of(TextBlock.builder().text("Strengths: Solid experience. Recommendations: Add certifications and headline metrics.").build()))
                .build();

        when(chatModel.stream(any(), any(), any()))
                .thenReturn(Flux.just(mockResponse));

        Map<String, Object> profileData = Map.of(
                "headline", "Software Engineer",
                "experience", "5 years Java, Spring, Reactive"
        );

        StepVerifier.create(agent.scanProfile(profileData))
                .assertNext(res -> {
                    assertThat(res).containsEntry("scanStatus", "COMPLETED");
                    assertThat(res).containsEntry("status", "SUCCESS");
                    assertThat(res).containsEntry("headline", "Software Engineer");
                    assertThat((String) res.get("profileAnalysis")).contains("Recommendations");
                })
                .verifyComplete();
    }

    @Test
    @DisplayName("Should reject execution if profile data map is empty or null")
    void shouldRejectEmptyProfileData() {
        StepVerifier.create(agent.scanProfile(Map.of()))
                .assertNext(res -> {
                    assertThat(res).containsEntry("scanStatus", "FAILED");
                    assertThat(res).containsEntry("status", "FAILED");
                    assertThat(res).containsEntry("errorCategory", "INVALID_INPUT");
                })
                .verifyComplete();

        StepVerifier.create(agent.scanProfile(null))
                .assertNext(res -> {
                    assertThat(res).containsEntry("scanStatus", "FAILED");
                    assertThat(res).containsEntry("status", "FAILED");
                    assertThat(res).containsEntry("errorCategory", "INVALID_INPUT");
                })
                .verifyComplete();
    }

    @Test
    @DisplayName("Should handle LLM failure gracefully and return error analysis status")
    void shouldHandleLlmFailureGracefully() {
        when(chatModel.stream(any(), any(), any()))
                .thenReturn(Flux.error(new RuntimeException("OpenAI API 500 Internal Error")));

        Map<String, Object> profileData = Map.of("headline", "DevOps Engineer");

        StepVerifier.create(agent.scanProfile(profileData))
                .assertNext(res -> {
                    assertThat(res).containsEntry("scanStatus", "FAILED");
                    assertThat(res).containsEntry("status", "FAILED");
                    assertThat(res).containsEntry("headline", "DevOps Engineer");
                })
                .verifyComplete();
    }
}
