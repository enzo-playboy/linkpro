package com.jobautomator;

import com.jobautomator.ratelimit.ReactiveRateLimiter;
import com.jobautomator.security.ProcessExecutionResult;
import com.jobautomator.security.SecureProcessExecutor;
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
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class JobAutomatorOrchestratorTest {

    @Mock
    private OpenAIChatModel chatModel;

    @Mock
    private SecureProcessExecutor processExecutor;

    private ReactiveRateLimiter rateLimiter;
    private JobAutomatorOrchestrator orchestrator;

    @BeforeEach
    void setUp() {
        rateLimiter = new ReactiveRateLimiter();
        orchestrator = new JobAutomatorOrchestrator(chatModel, processExecutor, rateLimiter);
    }

    @Test
    @DisplayName("Should reject pipeline execution if keywords list is empty or null")
    void shouldRejectEmptyKeywords() {
        StepVerifier.create(orchestrator.processJobApplicationsPipeline(List.of(), "Remote"))
                .assertNext(result -> {
                    assertThat(result).containsEntry("status", "FAILED");
                    assertThat(result).containsEntry("errorCategory", "INVALID_INPUT");
                })
                .verifyComplete();

        StepVerifier.create(orchestrator.processJobApplicationsPipeline(null, "Remote"))
                .assertNext(result -> {
                    assertThat(result).containsEntry("status", "FAILED");
                    assertThat(result).containsEntry("errorCategory", "INVALID_INPUT");
                })
                .verifyComplete();
    }

    @Test
    @DisplayName("Should reject pipeline execution if location is blank or null")
    void shouldRejectBlankLocation() {
        StepVerifier.create(orchestrator.processJobApplicationsPipeline(List.of("Java Developer"), "  "))
                .assertNext(result -> {
                    assertThat(result).containsEntry("status", "FAILED");
                    assertThat(result).containsEntry("errorCategory", "INVALID_INPUT");
                })
                .verifyComplete();
    }

    @Test
    @DisplayName("Should process jobs successfully when score is >= 75%")
    void shouldProcessHighMatchJobs() {
        // Mock score response: 88
        ChatResponse scoreResponse = ChatResponse.builder()
                .content(List.of(TextBlock.builder().text("88").build()))
                .build();
        // Mock cover letter response
        ChatResponse letterResponse = ChatResponse.builder()
                .content(List.of(TextBlock.builder().text("Prezados, sou especialista em Java Reativo.").build()))
                .build();

        when(chatModel.stream(any(), any(), any()))
                .thenReturn(Flux.just(scoreResponse))
                .thenReturn(Flux.just(letterResponse));

        // Mock safe BrowserGym execution
        when(processExecutor.executePythonScript(anyString(), any()))
                .thenReturn(Mono.just(new ProcessExecutionResult(0, "Application successfully sent", "", 500)));

        StepVerifier.create(orchestrator.processJobApplicationsPipeline(List.of("Java Developer"), "Remote"))
                .assertNext(result -> {
                    assertThat(result).containsEntry("status", "SUCCESS");
                    assertThat((Integer) result.get("totalProcessed")).isEqualTo(1);

                    @SuppressWarnings("unchecked")
                    List<Map<String, Object>> jobs = (List<Map<String, Object>>) result.get("results");
                    assertThat(jobs).hasSize(1);
                    Map<String, Object> job = jobs.get(0);
                    assertThat(job.get("matchScore")).isEqualTo(88.0);
                    assertThat(job.get("applicationStatus")).isEqualTo("SUBMITTED");
                    assertThat(job.get("coverLetterText")).isEqualTo("Prezados, sou especialista em Java Reativo.");
                })
                .verifyComplete();
    }

    @Test
    @DisplayName("Should filter out jobs when match score is below 75%")
    void shouldFilterLowMatchJobs() {
        // Mock score response: 40 (below threshold)
        ChatResponse scoreResponse = ChatResponse.builder()
                .content(List.of(TextBlock.builder().text("40").build()))
                .build();

        when(chatModel.stream(any(), any(), any()))
                .thenReturn(Flux.just(scoreResponse));

        StepVerifier.create(orchestrator.processJobApplicationsPipeline(List.of("Marketing Manager"), "Remote"))
                .assertNext(result -> {
                    assertThat(result).containsEntry("status", "SUCCESS");
                    assertThat((Integer) result.get("totalProcessed")).isEqualTo(0);

                    @SuppressWarnings("unchecked")
                    List<Map<String, Object>> jobs = (List<Map<String, Object>>) result.get("results");
                    assertThat(jobs).isEmpty();
                })
                .verifyComplete();
    }

    @Test
    @DisplayName("Should handle AI score failure with fallback 50.0 score")
    void shouldHandleAiScoreFailureResiliently() {
        // Mock failure from OpenAI
        when(chatModel.stream(any(), any(), any()))
                .thenReturn(Flux.error(new RuntimeException("Rate limit on OpenAI: sk-secret1234567890abcdef")));

        StepVerifier.create(orchestrator.processJobApplicationsPipeline(List.of("Java Developer"), "Remote"))
                .assertNext(result -> {
                    // Score falls back to 50.0, filtered out since < 75.0
                    assertThat(result).containsEntry("status", "SUCCESS");
                    assertThat((Integer) result.get("totalProcessed")).isEqualTo(0);
                })
                .verifyComplete();
    }

    @Test
    @DisplayName("Should handle BrowserGym failure gracefully without halting pipeline")
    void shouldHandleBrowserGymFailureGracefully() {
        ChatResponse scoreResponse = ChatResponse.builder()
                .content(List.of(TextBlock.builder().text("90").build()))
                .build();
        ChatResponse letterResponse = ChatResponse.builder()
                .content(List.of(TextBlock.builder().text("Cover letter text").build()))
                .build();

        when(chatModel.stream(any(), any(), any()))
                .thenReturn(Flux.just(scoreResponse))
                .thenReturn(Flux.just(letterResponse));

        // Subprocess returns non-zero code
        when(processExecutor.executePythonScript(anyString(), any()))
                .thenReturn(Mono.just(new ProcessExecutionResult(1, "", "Captcha encountered", 300)));

        StepVerifier.create(orchestrator.processJobApplicationsPipeline(List.of("Java Developer"), "Remote"))
                .assertNext(result -> {
                    assertThat(result).containsEntry("status", "SUCCESS");
                    assertThat((Integer) result.get("totalProcessed")).isEqualTo(1);

                    @SuppressWarnings("unchecked")
                    List<Map<String, Object>> jobs = (List<Map<String, Object>>) result.get("results");
                    Map<String, Object> job = jobs.get(0);
                    assertThat(job.get("applicationStatus")).isEqualTo("REQUIRES_MANUAL");
                })
                .verifyComplete();
    }
}
