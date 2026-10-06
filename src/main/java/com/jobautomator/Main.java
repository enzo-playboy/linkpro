package com.jobautomator;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.List;

public class Main {
    private static final Logger log = LoggerFactory.getLogger(Main.class);

    public static void main(String[] args) {
        log.info("=== Starting JobAutomator AI Platform ===");
        
        JobAutomatorOrchestrator orchestrator = new JobAutomatorOrchestrator();
        
        // ⚠️ .block() is ONLY used here because this is a runnable CLI main() method
        var result = orchestrator.processJobApplicationsPipeline(
                List.of("Java Developer", "AI Engineer"),
                "Remote"
        ).block();

        log.info("Pipeline Execution Completed: {}", result);
    }
}
