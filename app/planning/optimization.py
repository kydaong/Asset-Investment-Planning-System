"""
Optimization Engine for Mode 3
Solves portfolio optimization problems (maximize NPV subject to constraints)
"""
from typing import List, Dict, Any, Optional
import random

class OptimizationEngine:
    """
    Portfolio optimization using greedy and genetic algorithms
    """
    
    def __init__(self):
        self.algorithms = {
            "greedy": self._greedy_optimization,
            "genetic": self._genetic_algorithm
        }
    
    def optimize(
        self,
        projects: List[Dict],
        budget: float,
        algorithm: str = "greedy",
        additional_constraints: Optional[Dict] = None
    ) -> Dict:
        """
        Optimize project portfolio
        
        Args:
            projects: List of candidate projects with cost, npv, etc.
            budget: Budget constraint
            algorithm: "greedy" or "genetic"
            additional_constraints: Other constraints (resource limits, etc.)
            
        Returns:
            Optimized portfolio with selected/deferred projects
        """
        
        if algorithm not in self.algorithms:
            algorithm = "greedy"
        
        optimizer = self.algorithms[algorithm]
        return optimizer(projects, budget, additional_constraints or {})
    
    def _greedy_optimization(
        self, 
        projects: List[Dict], 
        budget: float,
        constraints: Dict
    ) -> Dict:
        """
        Greedy algorithm: Sort by NPV/Cost ratio, select until budget exhausted
        Fast and works well for most cases
        """
        
        # Calculate efficiency (NPV per dollar spent) for each project
        for project in projects:
            cost = project.get("estimated_cost", 1)
            npv = project.get("npv", 0)
            
            # Efficiency = NPV / Cost
            project["efficiency"] = npv / cost if cost > 0 else 0
            
            project["efficiency"] = npv /cost if cost>0 else 0
            
            # Also calculate risk-adjusted NPV
            risk_factor = {
                "Low": 1.0,
                "Medium": 0.85,
                "High": 0.70
            }.get(project.get("risk_level", "Medium"), 0.85)
            
            project["risk_adjusted_npv"] = npv * risk_factor
            project["risk_adjusted_efficiency"] = project["risk_adjusted_npv"] / cost if cost > 0 else 0
        
        # Sort by efficiency (highest first)
        sorted_projects = sorted(
            projects, 
            key=lambda p: p["risk_adjusted_efficiency"], 
            reverse=True
        )
        
        # Select projects until budget exhausted
        selected = []
        total_cost = 0
        total_npv = 0
        total_risk_adjusted_npv = 0
        
        for project in sorted_projects:
            project_cost = project.get("estimated_cost", 0)
            
            if total_cost + project_cost <= budget:
                selected.append(project)
                total_cost += project_cost
                total_npv += project.get("npv", 0)
                total_risk_adjusted_npv += project.get("risk_adjusted_npv", 0)
        
        # Deferred projects
        deferred = [p for p in sorted_projects if p not in selected]
        
        # Calculate portfolio metrics
        selected_count = len(selected)
        avg_irr = sum(p.get("irr", 0) for p in selected) / selected_count if selected_count > 0 else 0
        
        # Count by priority
        priority_breakdown = {}
        for p in selected:
            priority = p.get("priority", "Medium")
            priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1
        
        # Count by category
        category_breakdown = {}
        for p in selected:
            category = p.get("project_type", "Unknown")
            category_breakdown[category] = category_breakdown.get(category, 0) + 1
        
        return {
            "selected_projects": selected,
            "deferred_projects": deferred,
            "total_cost": total_cost,
            "total_npv": total_npv,
            "total_risk_adjusted_npv": total_risk_adjusted_npv,
            "budget_used": total_cost,
            "budget_remaining": budget - total_cost,
            "budget_utilization_pct": (total_cost / budget * 100) if budget > 0 else 0,
            "project_count": selected_count,
            "avg_irr": avg_irr,
            "priority_breakdown": priority_breakdown,
            "category_breakdown": category_breakdown,
            "algorithm": "greedy"
        }
    
    def _genetic_algorithm(
        self, 
        projects: List[Dict], 
        budget: float,
        constraints: Dict
    ) -> Dict:
        """
        Genetic algorithm for complex optimization
        Better for large portfolios but slower
        """
        population_size = 50
        generations = 100
        mutation_rate = 0.05
        
        n_projects = len(projects)
        
        # Initialize random population
        population = []
        for _ in range(population_size):
            # Random binary chromosome (1 = include, 0 = exclude)
            chromosome = [random.randint(0, 1) for _ in range(n_projects)]
            
            # Repair: ensure budget constraint
            while self._calc_cost(chromosome, projects) > budget:
                included_indices = [i for i, gene in enumerate(chromosome) if gene == 1]
                if not included_indices:
                    break
                chromosome[random.choice(included_indices)] = 0
            
            population.append(chromosome)
        
        # Evolve
        for gen in range(generations):
            # Calculate fitness for each individual
            fitness_scores = [
                self._calc_npv(chrom, projects) 
                if self._calc_cost(chrom, projects) <= budget 
                else 0 
                for chrom in population
            ]
            
            # Selection (tournament)
            new_population = []
            for _ in range(population_size):
                # Tournament: pick 3 random, select best
                tournament = random.sample(list(zip(population, fitness_scores)), min(3, len(population)))
                winner = max(tournament, key=lambda x: x[1])[0]
                new_population.append(winner[:])  # Copy
            
            # Crossover
            for i in range(0, population_size - 1, 2):
                if random.random() < 0.7:  # 70% crossover rate
                    point = random.randint(1, n_projects - 1)
                    new_population[i][point:], new_population[i+1][point:] = \
                        new_population[i+1][point:], new_population[i][point:]
            
            # Mutation
            for chromosome in new_population:
                for i in range(n_projects):
                    if random.random() < mutation_rate:
                        chromosome[i] = 1 - chromosome[i]
                
                # Repair budget constraint
                while self._calc_cost(chromosome, projects) > budget:
                    included = [i for i, gene in enumerate(chromosome) if gene == 1]
                    if not included:
                        break
                    chromosome[random.choice(included)] = 0
            
            population = new_population
        
        # Get best solution
        fitness_scores = [
            self._calc_npv(chrom, projects) 
            if self._calc_cost(chrom, projects) <= budget 
            else 0 
            for chrom in population
        ]
        best_chromosome = population[fitness_scores.index(max(fitness_scores))]
        
        # Build result
        selected = [p for i, p in enumerate(projects) if best_chromosome[i] == 1]
        deferred = [p for i, p in enumerate(projects) if best_chromosome[i] == 0]
        
        total_cost = sum(p.get("estimated_cost", 0) for p in selected)
        total_npv = sum(p.get("npv", 0) for p in selected)
        
        selected_count = len(selected)
        avg_irr = sum(p.get("irr", 0) for p in selected) / selected_count if selected_count > 0 else 0
        
        return {
            "selected_projects": selected,
            "deferred_projects": deferred,
            "total_cost": total_cost,
            "total_npv": total_npv,
            "budget_used": total_cost,
            "budget_remaining": budget - total_cost,
            "budget_utilization_pct": (total_cost / budget * 100) if budget > 0 else 0,
            "project_count": selected_count,
            "avg_irr": avg_irr,
            "algorithm": "genetic"
        }
    
    def _calc_cost(self, chromosome: List[int], projects: List[Dict]) -> float:
        """Calculate total cost of a chromosome"""
        return sum(
            projects[i].get("estimated_cost", 0) 
            for i, gene in enumerate(chromosome) if gene == 1
        )
    
    def _calc_npv(self, chromosome: List[int], projects: List[Dict]) -> float:
        """Calculate total NPV of a chromosome"""
        return sum(
            projects[i].get("npv", 0) 
            for i, gene in enumerate(chromosome) if gene == 1
        )
    
    def analyze_sensitivity(
        self,
        projects: List[Dict],
        base_budget: float,
        budget_range: List[float]
    ) -> List[Dict]:
        """
        Sensitivity analysis: how does portfolio change with budget
        
        Args:
            projects: Candidate projects
            base_budget: Base budget
            budget_range: List of budget values to test (e.g., [10M, 12M, 15M, 18M, 20M])
            
        Returns:
            List of optimization results for each budget value
        """
        results = []
        
        for budget in budget_range:
            result = self.optimize(projects, budget, algorithm="greedy")
            result["budget_scenario"] = budget
            results.append(result)
        
        return results
    
    def compare_algorithms(
        self,
        projects: List[Dict],
        budget: float
    ) -> Dict:
        """
        Compare greedy vs genetic algorithm results
        """
        greedy_result = self.optimize(projects, budget, algorithm="greedy")
        genetic_result = self.optimize(projects, budget, algorithm="genetic")
        
        return {
            "greedy": greedy_result,
            "genetic": genetic_result,
            "npv_difference": genetic_result["total_npv"] - greedy_result["total_npv"],
            "npv_improvement_pct": (
                (genetic_result["total_npv"] - greedy_result["total_npv"]) / 
                greedy_result["total_npv"] * 100
            ) if greedy_result["total_npv"] > 0 else 0
        }