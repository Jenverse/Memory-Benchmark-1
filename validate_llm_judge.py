import csv
from collections import defaultdict

# Read the answer key CSV
llm_judge_ratings = []
test_ids = []
with open('human_validation/answer_key.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        llm_judge_ratings.append(row['llm_judge_rating'].lower().strip())
        test_ids.append(row['test_id'])

# User's CORRECTED answers (human validation)
human_answers_raw = """incorrect
correct
correct
correct
correct
incorrect
partially_correct
correct
Partially correct
correct
incorrect
correct
incorrect
correct
partially correct
correct
partially correct
correct
Partially correct
correct
correct
Partially correct
incorrect
Partially correct
correct
correct
incorrect
Partially correct
correct
Partially correct"""

human_answers = [ans.lower().strip() for ans in human_answers_raw.strip().split('\n')]

# Normalize "partially correct" vs "partially_correct"
def normalize(rating):
    rating = rating.replace('_', ' ')
    return rating

llm_judge_ratings = [normalize(r) for r in llm_judge_ratings]
human_answers = [normalize(r) for r in human_answers]

# Open output file
with open('llm_judge_validation_results.txt', 'w') as out:
    out.write("=" * 70 + "\n")
    out.write("LLM-as-a-Judge Validation Results\n")
    out.write("=" * 70 + "\n\n")
    
    out.write(f"Total test cases: {len(llm_judge_ratings)}\n")
    out.write(f"Human answers provided: {len(human_answers)}\n\n")
    
    # Calculate agreement
    agreements = 0
    disagreements = []
    
    for i, (llm, human, test_id) in enumerate(zip(llm_judge_ratings, human_answers, test_ids), 1):
        if llm == human:
            agreements += 1
        else:
            disagreements.append({
                'id': i,
                'test_id': test_id,
                'llm_judge': llm,
                'human': human
            })
    
    accuracy = agreements / len(llm_judge_ratings) * 100
    
    out.write(f"✅ Agreement: {agreements}/{len(llm_judge_ratings)} ({accuracy:.1f}%)\n")
    out.write(f"❌ Disagreement: {len(disagreements)}/{len(llm_judge_ratings)} ({100-accuracy:.1f}%)\n\n")
    
    if disagreements:
        out.write("Disagreements:\n")
        out.write("-" * 70 + "\n")
        for d in disagreements:
            out.write(f"  Test {d['id']:2d} ({d['test_id']}): LLM Judge = '{d['llm_judge']:20s}' | Human = '{d['human']}'\n")
        out.write("\n")
    
    # Confusion matrix
    confusion = defaultdict(lambda: defaultdict(int))
    
    for llm, human in zip(llm_judge_ratings, human_answers):
        confusion[llm][human] += 1
    
    out.write("Confusion Matrix (LLM Judge vs Human):\n")
    out.write("-" * 70 + "\n")
    out.write(f"{'LLM Judge \\ Human':<25} {'correct':<15} {'incorrect':<15} {'partially correct':<15}\n")
    out.write("-" * 70 + "\n")
    
    for llm_rating in ['correct', 'incorrect', 'partially correct']:
        row = f'{llm_rating:<25}'
        for human_rating in ['correct', 'incorrect', 'partially correct']:
            row += f'{confusion[llm_rating][human_rating]:<15}'
        out.write(row + "\n")
    
    out.write("\n")
    
    # Calculate per-category accuracy
    out.write('Per-Category Agreement:\n')
    out.write("-" * 70 + "\n")
    correct_count = sum(1 for llm, human in zip(llm_judge_ratings, human_answers) if llm == 'correct' and human == 'correct')
    incorrect_count = sum(1 for llm, human in zip(llm_judge_ratings, human_answers) if llm == 'incorrect' and human == 'incorrect')
    partial_count = sum(1 for llm, human in zip(llm_judge_ratings, human_answers) if llm == 'partially correct' and human == 'partially correct')
    
    total_correct = sum(1 for r in llm_judge_ratings if r == 'correct')
    total_incorrect = sum(1 for r in llm_judge_ratings if r == 'incorrect')
    total_partial = sum(1 for r in llm_judge_ratings if r == 'partially correct')
    
    total_human_correct = sum(1 for r in human_answers if r == 'correct')
    total_human_incorrect = sum(1 for r in human_answers if r == 'incorrect')
    total_human_partial = sum(1 for r in human_answers if r == 'partially correct')
    
    out.write(f"When LLM Judge said 'correct':           {correct_count}/{total_correct} agreed ({correct_count/total_correct*100:.1f}%)\n")
    out.write(f"When LLM Judge said 'incorrect':         {incorrect_count}/{total_incorrect} agreed ({incorrect_count/total_incorrect*100:.1f}%)\n")
    out.write(f"When LLM Judge said 'partially correct': {partial_count}/{total_partial} agreed ({partial_count/total_partial*100:.1f}%)\n")
    out.write("\n")
    out.write(f"When Human said 'correct':           {correct_count}/{total_human_correct} agreed ({correct_count/total_human_correct*100:.1f}%)\n")
    out.write(f"When Human said 'incorrect':         {incorrect_count}/{total_human_incorrect} agreed ({incorrect_count/total_human_incorrect*100:.1f}%)\n")
    out.write(f"When Human said 'partially correct': {partial_count}/{total_human_partial} agreed ({partial_count/total_human_partial*100:.1f}%)\n")
    out.write("\n")
    out.write("=" * 70 + "\n")

print("✅ Analysis complete! Results saved to llm_judge_validation_results.txt")

