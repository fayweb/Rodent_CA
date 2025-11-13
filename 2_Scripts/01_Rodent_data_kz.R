# ================================================================
# GBIF RODENT OCCURRENCE ANALYSIS FOR CENTRAL ASIA - KAZAKHSTAN
# ================================================================
# Repository: Rodent_CA
# Purpose: Analyze GBIF rodent data for surveillance protocol development
# Data: Kazakhstan Rodentia occurrences from GBIF
# Author: Fay Webster, ZSL
# Date: November 2025
# ================================================================

# Load required packages
library(tidyverse)
library(sf)
library(rnaturalearth)
library(rnaturalearthdata)
library(viridis)
library(scales)
library(patchwork)
library(lubridate)
library(cowplot)

# Check if we're in the project directory
if (!file.exists("Rodent_CA.Rproj")) {
    stop("Please set working directory to project root (where Rodent_CA.Rproj is located)")
}

# Set theme for all plots
theme_set(theme_minimal(base_size = 11))


# ================================================================
# STEP 1: READ GBIF DATA
# ================================================================

cat("Reading Kazakhstan rodent data...\n")

gbif_data_raw <- read.csv("1_Data_Sets/01_GBIF/Rodents_kazakhstan.csv", 
                          sep = "\t")

cat("Raw data dimensions:", nrow(gbif_data_raw), "rows x", 
    ncol(gbif_data_raw), "columns\n\n")

# Check column names to see what we have
cat("Available columns:\n")
print(names(gbif_data_raw))
cat("\n")

# ================================================================
# STEP 2: DATA CLEANING AND FILTERING
# ================================================================

cat("Cleaning and filtering data...\n")

# Adapt column selection based on what's actually in your CSV
gbif_clean <- gbif_data_raw %>%
    # Remove records without species ID or coordinates
    filter(
        !is.na(species),
        !is.na(decimalLatitude),
        !is.na(decimalLongitude)
    ) %>%
    # Add year if not present (extract from eventDate if needed)
    mutate(
        year = if_else(
            is.na(year) & !is.na(eventDate),
            year(ymd_hms(eventDate, quiet = TRUE)),
            year
        )
    ) %>%
    # Filter for quality and recency
    filter(
        year >= 1950 | is.na(year),
        coordinateUncertaintyInMeters < 10000 | is.na(coordinateUncertaintyInMeters)
    ) %>%
    # Add useful derived variables
    mutate(
        decade = if_else(!is.na(year), floor(year / 10) * 10, NA_real_),
        recent = if_else(year >= 2000, "2000-present", "1950-1999", missing = "Unknown"),
        genus = word(species, 1),
        species_binomial = paste(word(species, 1), word(species, 2)),
        # Body mass category (rough estimates from taxonomy)
        body_mass_category = case_when(
            genus %in% c("Rhombomys", "Spermophilus", "Marmota") ~ "Large (150-250g)",
            genus %in% c("Meriones", "Cricetulus", "Ochotona") ~ "Medium (50-150g)",
            genus %in% c("Apodemus", "Mus", "Microtus", "Rattus") ~ "Small (20-50g)",
            genus %in% c("Sorex", "Crocidura") ~ "Very small (5-20g)",
            TRUE ~ "Unknown"
        ),
        # Zoonotic priority
        zoonotic_priority = case_when(
            genus == "Rhombomys" ~ "CRITICAL - Plague reservoir",
            genus == "Meriones" ~ "CRITICAL - Plague reservoir",
            genus %in% c("Microtus", "Myodes") ~ "HIGH - Hantavirus",
            genus %in% c("Apodemus", "Rattus") ~ "HIGH - Multi-pathogen",
            genus == "Ochotona" ~ "CRITICAL - Plague/tularemia",
            genus == "Cricetulus" ~ "MEDIUM - Plague/hantavirus",
            TRUE ~ "LOW"
        )
    )

# Summary statistics
cat("\n=== DATA CLEANING SUMMARY ===\n")
cat("Records after filtering:", nrow(gbif_clean), "\n")
cat("Unique species:", n_distinct(gbif_clean$species), "\n")
cat("Date range:", min(gbif_clean$year, na.rm = TRUE), "-", 
    max(gbif_clean$year, na.rm = TRUE), "\n")
cat("Coordinates available:", sum(!is.na(gbif_clean$decimalLatitude)), "\n\n")

# ================================================================
# STEP 3: SPECIES RANKING
# ================================================================

cat("Calculating species rankings...\n")

species_summary <- gbif_clean %>%
    count(species, genus, family, zoonotic_priority, body_mass_category, 
          name = "n_records") %>%
    arrange(desc(n_records)) %>%
    mutate(
        rank = row_number(),
        cumulative_prop = cumsum(n_records) / sum(n_records)
    )

cat("\n=== TOP 50 SPECIES ===\n")
print(species_summary %>% 
          slice_head(n = 50) %>% 
          select(Rank = rank, Species = species, Records = n_records, 
                 Priority = zoonotic_priority))
cat("\n")

# Export
write_csv(species_summary, "4_Tables/species_summary_kazakhstan.csv")

# ================================================================
# VISUALIZATION 1: SPECIES ABUNDANCE
# ================================================================

cat("Creating species abundance plot...\n")

plot1_abundance <- species_summary %>%
    slice_head(n = 20) %>%
    ggplot(aes(x = reorder(species, n_records), y = n_records, 
               fill = zoonotic_priority)) +
    geom_col(alpha = 0.85, width = 0.7) +
    geom_text(aes(label = comma(n_records)), hjust = -0.2, size = 3) +
    coord_flip() +
    scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.15))) +
    scale_fill_manual(
        values = c(
            "CRITICAL - Plague reservoir" = "#D7191C",
            "CRITICAL - Plague/tularemia" = "#E64B35",
            "HIGH - Hantavirus" = "#FDAE61",
            "HIGH - Multi-pathogen" = "#FEE08B",
            "MEDIUM - Plague/hantavirus" = "#ABDDA4",
            "LOW" = "#2B83BA"
        ),
        name = "Zoonotic Priority"
    ) +
    labs(
        title = "Most Common Rodent Species in Kazakhstan",
        subtitle = paste0("Based on ", comma(nrow(gbif_clean)), " GBIF occurrence records"),
        x = NULL,
        y = "Number of occurrence records",
        caption = "Data: GBIF.org (2025)"
    ) +
    theme(
        axis.text.y = element_text(face = "italic", size = 9),
        plot.title = element_text(face = "bold", size = 14),
        legend.position = "bottom",
        panel.grid.minor = element_blank()
    ) +
    guides(fill = guide_legend(nrow = 2))

ggsave("3_Figures/01_species_abundance_kazakhstan.pdf", plot1_abundance,
       width = 10, height = 8, device = cairo_pdf)
ggsave("3_Figures/01_species_abundance_kazakhstan.png", plot1_abundance,
       width = 10, height = 8, dpi = 300)

# ================================================================
# VISUALIZATION 2: CUMULATIVE CURVE
# ================================================================

cat("Creating cumulative species curve...\n")

plot2_cumulative <- species_summary %>%
    ggplot(aes(x = rank, y = cumulative_prop * 100)) +
    geom_line(color = "#2C7BB6", linewidth = 1.2) +
    geom_point(color = "#2C7BB6", size = 2) +
    geom_hline(yintercept = 80, linetype = "dashed", 
               color = "#D7191C", linewidth = 0.8) +
    annotate("text", x = max(species_summary$rank) * 0.7, y = 85,
             label = "80% of records", color = "#D7191C", size = 4) +
    scale_y_continuous(labels = function(x) paste0(x, "%"),
                       breaks = seq(0, 100, 20)) +
    labs(
        title = "Species Accumulation Curve",
        subtitle = "How many species account for most observations?",
        x = "Species rank (by abundance)",
        y = "Cumulative percentage of all records",
        caption = paste0("Top ", sum(species_summary$cumulative_prop <= 0.8), 
                         " species account for 80% of records")
    ) +
    theme(plot.title = element_text(face = "bold"))

ggsave("3_Figures/02_cumulative_curve.pdf", plot2_cumulative,
       width = 8, height = 6, device = cairo_pdf)

# ================================================================
# VISUALIZATION 3: GEOGRAPHIC MAP - ALL SPECIES
# ================================================================

cat("Creating geographic distribution map...\n")

# Get Kazakhstan boundary
kazakhstan <- ne_countries(country = "kazakhstan", scale = "medium", 
                           returnclass = "sf")

plot3_map <- ggplot() +
    geom_sf(data = kazakhstan, fill = "grey95", color = "grey50", linewidth = 0.5) +
    geom_point(data = gbif_clean,
               aes(x = decimalLongitude, y = decimalLatitude, 
                   color = zoonotic_priority),
               alpha = 0.6, size = 1.5) +
    scale_color_manual(
        values = c(
            "CRITICAL - Plague reservoir" = "#D7191C",
            "CRITICAL - Plague/tularemia" = "#E64B35",
            "HIGH - Hantavirus" = "#FDAE61",
            "HIGH - Multi-pathogen" = "#FEE08B",
            "MEDIUM - Plague/hantavirus" = "#ABDDA4",
            "LOW" = "#2B83BA"
        ),
        name = "Zoonotic Priority"
    ) +
    coord_sf() +
    labs(
        title = "Geographic Distribution of Rodent Occurrences",
        subtitle = paste0("Kazakhstan (n = ", comma(nrow(gbif_clean)), " records)"),
        x = "Longitude",
        y = "Latitude",
        caption = "Data: GBIF.org (2025)"
    ) +
    theme(
        plot.title = element_text(face = "bold", size = 13),
        legend.position = "bottom"
    ) +
    guides(color = guide_legend(override.aes = list(size = 3, alpha = 1)))

ggsave("3_Figures/03_map_all_species.pdf", plot3_map,
       width = 10, height = 7, device = cairo_pdf)

# ================================================================
# VISUALIZATION 4: CRITICAL SPECIES FOCUS
# ================================================================

cat("Creating critical species map...\n")

critical_species <- gbif_clean %>%
    filter(str_detect(zoonotic_priority, "CRITICAL"))

if (nrow(critical_species) > 0) {
    
    plot4_critical <- ggplot() +
        geom_sf(data = kazakhstan, fill = "grey95", color = "grey50") +
        geom_point(data = critical_species,
                   aes(x = decimalLongitude, y = decimalLatitude, 
                       color = genus, size = recent),
                   alpha = 0.7) +
        scale_color_manual(
            values = c("Rhombomys" = "#D7191C", "Meriones" = "#E64B35",
                       "Ochotona" = "#FD8D3C"),
            name = "Genus"
        ) +
        scale_size_manual(
            values = c("1950-1999" = 1.5, "2000-present" = 3, "Unknown" = 2),
            name = "Time Period"
        ) +
        coord_sf() +
        labs(
            title = "CRITICAL PRIORITY: Plague Reservoir Species",
            subtitle = paste0("n = ", nrow(critical_species), " records"),
            x = "Longitude",
            y = "Latitude",
            caption = "Larger points = more recent observations"
        ) +
        theme(
            plot.title = element_text(face = "bold", color = "#D7191C", size = 13),
            legend.position = "bottom"
        )
    
    ggsave("3_Figures/04_critical_species_map.pdf", plot4_critical,
           width = 10, height = 7, device = cairo_pdf)
}

# ================================================================
# VISUALIZATION 5: TEMPORAL TRENDS
# ================================================================

cat("Creating temporal trends plot...\n")

temporal_data <- gbif_clean %>%
    filter(!is.na(year), year >= 1950) %>%
    count(year, genus) %>%
    group_by(year) %>%
    mutate(total_year = sum(n))

plot5_temporal <- temporal_data %>%
    ggplot(aes(x = year, y = n, fill = genus)) +
    geom_col(position = "stack", alpha = 0.85) +
    scale_fill_viridis_d(option = "turbo", name = "Genus") +
    scale_x_continuous(breaks = seq(1950, 2025, 10)) +
    scale_y_continuous(labels = comma) +
    labs(
        title = "Temporal Trends in Rodent Documentation",
        subtitle = "Number of occurrence records per year",
        x = "Year",
        y = "Number of records",
        caption = "Recent increases likely reflect digitization efforts"
    ) +
    theme(
        plot.title = element_text(face = "bold"),
        legend.position = "right"
    )

ggsave("3_Figures/05_temporal_trends.pdf", plot5_temporal,
       width = 12, height = 6, device = cairo_pdf)

# ================================================================
# CREATE SUMMARY TABLE FOR PROTOCOL
# ================================================================

cat("Creating trap recommendation table...\n")

trap_table <- species_summary %>%
    slice_head(n = 20) %>%
    mutate(
        trap_recommendation = case_when(
            body_mass_category == "Large (150-250g)" ~ "Large Sherman or Tomahawk",
            body_mass_category == "Medium (50-150g)" ~ "Large Sherman",
            body_mass_category == "Small (20-50g)" ~ "Large Sherman or Longworth",
            body_mass_category == "Very small (5-20g)" ~ "Longworth (HIGH MORTALITY RISK)",
            TRUE ~ "Large Sherman"
        )
    ) %>%
    select(
        Rank = rank,
        Species = species,
        Genus = genus,
        Family = family,
        Records = n_records,
        `Body Mass` = body_mass_category,
        `Zoonotic Priority` = zoonotic_priority,
        `Trap Recommendation` = trap_recommendation
    )

write_csv(trap_table, "4_Tables/trap_recommendations_kazakhstan.csv")

# ================================================================
# FINAL SUMMARY
# ================================================================

summary_report <- list(
    total_records = nrow(gbif_clean),
    total_species = n_distinct(gbif_clean$species),
    critical_species = sum(str_detect(species_summary$zoonotic_priority, "CRITICAL")),
    date_range = paste(min(gbif_clean$year, na.rm = TRUE), "-", 
                       max(gbif_clean$year, na.rm = TRUE)),
    most_common = species_summary$species[1],
    top_10 = species_summary$species[1:10]
)

# Save summary
write_rds(summary_report, "5_Outputs/analysis_summary.rds")

# Print summary
cat("\n", "===============================================\n")
cat("ANALYSIS COMPLETE!\n")
cat("===============================================\n\n")

cat("OUTPUTS CREATED:\n")
cat("- 5 figures in 3_Figures/\n")
cat("- 2 data tables in 4_Tables/\n")
cat("- 1 summary object in 5_Outputs/\n\n")

cat("KEY FINDINGS:\n")
cat("- Total records:", comma(summary_report$total_records), "\n")
cat("- Total species:", summary_report$total_species, "\n")
cat("- CRITICAL priority species:", summary_report$critical_species, "\n")
cat("- Most common:", summary_report$most_common, "\n")
cat("- Date range:", summary_report$date_range, "\n\n")

cat("Next steps:\n")
cat("1. Review figures in 3_Figures/\n")
cat("2. Check trap recommendations in 4_Tables/\n")
cat("3. Integrate into protocol document\n")
cat("4. Repeat for other Central Asian countries\n\n")

# Session info for reproducibility
writeLines(capture.output(sessionInfo()), "5_Outputs/session_info.txt")

cat("Done! 🎉\n")