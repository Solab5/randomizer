# Functions to do the sampling
import pandas as pd

def get_sample_sizes(village_count, threshold=100, male_prop=0.6, female_prop=0.2, youth_prop=0.2):
    if village_count >= threshold:
        return int(male_prop * 30), int(female_prop * 30), int(youth_prop * 30)
    else:
        return int(0.5 * 24), int(0.25 * 24), int(0.25 * 24)
    
def sample_data(data, gender_group, sample_size_prop, label):
    filtered_data = data.query("`HHHeadship` == @label")
    if len(filtered_data) <= sample_size_prop:
        return filtered_data.copy()  # Return all data if remaining is less than sample size
    else:
        return filtered_data.sample(n=sample_size_prop)
    
def sample_village(df, village_counts, male_prop=0.6, female_prop=0.2, youth_prop=0.2, threshold=100):
    def get_samples(x):
        village_name = x['village'].iloc[0]
        village_size = village_counts.get(village_name, 0)

        if village_size <= 30:  # Check if the village has 30 or fewer households
            return x.copy()  # Assign all households as targets without sampling

        male_sample_size, female_sample_size, youth_sample_size = get_sample_sizes(village_size)

        males = sample_data(x.copy(), 'Male Headed', male_sample_size, 'Male Headed')
        females = sample_data(x.copy(), 'Female Headed', female_sample_size, 'Female Headed')
        youths = sample_data(x.copy(), 'Youth Headed', youth_sample_size, 'Youth Headed')

        return pd.concat([males, females, youths])

    # Sample target data
    target_samples = df.groupby('village', group_keys=False).apply(get_samples)
    target_samples['status'] = 'target'

    # Drop target rows and get reserve data
    reserve_data = df.drop(target_samples.index)

    # Sample reserve data
    reserve_samples = reserve_data.groupby('village', group_keys=False).apply(get_samples)
    reserve_samples['status'] = 'reserve'

    # Combine target and reserve samples
    return pd.concat([target_samples, reserve_samples])

# def get_final_df(df, village_counts, male_prop=0.6, female_prop=0.2, youth_prop=0.2, threshold=100):
#     # Estimate total iterations based on village counts (assuming sampling per village)
#     total_iterations = len(village_counts)

#     with st.spinner("Generating Sampled Data..."):
#         progress_bar = st.progress(0)
#         df_sampled = sample_village(df.copy(), village_counts, male_prop, female_prop, youth_prop, threshold)

#         # Update progress bar for each village processed
#         for i in range(len(village_counts)):
#             progress_bar.progress(i + 1 / total_iterations)

#     return df_sampled

def get_final_df(df, village_counts, male_prop=0.6, female_prop=0.2, youth_prop=0.2, threshold=100):
    df_sampled = sample_village(df.copy(), village_counts, male_prop, female_prop, youth_prop, threshold)
    return df_sampled